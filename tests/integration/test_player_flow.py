from fastapi.testclient import TestClient
from app import app
from services.auth_service import auth_service
from database.db_manager import DatabaseManager
from unittest.mock import patch
import pytest
import time
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from config.settings import get_settings

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Configura um banco de dados de teste limpo antes de cada teste"""
    # Limpar banco de teste se existir
    settings = get_settings()
    
    if os.path.exists(settings.DB_FILE_PATH):
        os.remove(settings.DB_FILE_PATH)
        
    # Configura banco de teste
    DatabaseManager().DB_FILE_PATH = settings.DB_FILE_PATH
    DatabaseManager().init_db()
    
    # Limpa dados existentes
    with DatabaseManager().get_connection() as conn:
        conn.execute("DELETE FROM players")
        conn.commit()
    
    yield
    
    # Limpa após os testes
    with DatabaseManager().get_connection() as conn:
        conn.execute("DELETE FROM players")
        conn.commit()

@pytest.fixture(autouse=True)
def setup_rate_limit():
    """Configura um novo limiter para os testes"""
    original_limiter = app.state.limiter
    test_limiter = Limiter(key_func=get_remote_address, default_limits=["15/minute"])
    app.state.limiter = test_limiter
    yield
    app.state.limiter = original_limiter

@pytest.fixture
def auth_token():
    return auth_service.generate_token()

@pytest.fixture
def test_player(auth_token):
    """Cria um jogador de teste no banco"""
    player_data = {
        "name": "TestPlayer",
        "tag": "BR1",
        "email": "test@example.com",
        "login": "testplayer",
        "password": "testpass123"
    }
    
    # Adiciona jogador via API
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/players/", json=player_data, headers=headers)
    assert response.status_code == 200
    return player_data

def test_player_flow_integration(auth_token, test_player):
    """Testa o fluxo completo de operações com jogador"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # 1. Verifica se o jogador foi criado corretamente
    response = client.get("/players/", headers=headers)
    assert response.status_code == 200
    players = response.json()
    assert any(p["name"] == test_player["name"] and p["tag"] == test_player["tag"] for p in players)
    
    # 2. Testa verificação de credenciais
    cred_check = {
        "login": test_player["login"],
        "email": test_player["email"]
    }
    response = client.post("/players/verify-credentials", json=cred_check, headers=headers)
    assert response.status_code == 200
    
    # 3. Busca rank do jogador (mockando apenas a chamada externa)
    expected_url = f"https://www.valking.gg/player?username={test_player['name']}%23{test_player['tag']}"
    with patch('services.player_service.PlayerService.fetch_rank_online') as mock_fetch:
        mock_fetch.return_value = {
            "message": "Por favor, consulte seu rank diretamente em:",
            "url": expected_url
        }
        
        response = client.get(
            f"/players/{test_player['name']}/{test_player['tag']}", 
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "rank" in data
        assert isinstance(data["rank"], dict)
        assert data["rank"]["message"] == "Por favor, consulte seu rank diretamente em:"
        assert data["rank"]["url"] == expected_url
        assert data["name"] == test_player["name"]
        assert data["tag"] == test_player["tag"]
        assert "password" in data

def test_rate_limiting_integration(auth_token, test_player):
    """Testa o rate limiting em um cenário real"""
    base_headers = {"Authorization": f"Bearer {auth_token}"}
    expected_url = f"https://www.valking.gg/player?username={test_player['name']}%23{test_player['tag']}"
    
    # Faz várias requisições rápidas
    with patch('services.player_service.PlayerService.fetch_rank_online') as mock_fetch:
        mock_fetch.return_value = {
            "message": "Por favor, consulte seu rank diretamente em:",
            "url": expected_url
        }
        
        # Primeiras requisições (dentro do limite)
        for i in range(14):
            response = client.get(
                f"/players/{test_player['name']}/{test_player['tag']}", 
                headers={
                    **base_headers,
                    "X-Forwarded-For": "192.168.1.1"
                }
            )
            assert response.status_code == 200
            time.sleep(0.1)
        
        # Última requisição (deve exceder o limite)
        response = client.get(
            f"/players/{test_player['name']}/{test_player['tag']}", 
            headers={
                **base_headers,
                "X-Forwarded-For": "192.168.1.1"
            }
        )
        assert response.status_code == 429
        error_response = response.json()
        
        # Verifica se a resposta contém a mensagem de erro em qualquer formato conhecido
        assert any(
            key in error_response and "rate limit" in error_response[key].lower()
            for key in ['detail', 'error', 'message']
        ), "Resposta não contém mensagem de rate limit em formato conhecido"

def test_invalid_authentication_integration():
    """Testa o fluxo de autenticação inválida"""
    headers = {"Authorization": "Bearer invalid_token"}
    
    response = client.get("/players/", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido"

    # Tenta acessar endpoint protegido sem token
    response = client.get("/players/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token não fornecido"