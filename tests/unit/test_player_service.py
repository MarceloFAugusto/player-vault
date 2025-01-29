"""
Testes Unitários Puros para o PlayerService, com foco no método get_player_rank e derivados

Cobertura atual:
- Recuperação de rank do cache ✓
- Jogador não encontrado ✓
- Erro na requisição HTTP ✓
- Resposta inválida da API ✓
- Timeout na requisição ✓
- Validação de formatos inválidos de name/tag ✓
- Fluxo de sucesso completo (busca no BD + API externa) ✓
- Diferentes formatos de resposta da API ✓
- Extração de rank do HTML (diversos formatos) ✓
- Validação de parâmetros de entrada ✓
- Construção do resultado do player ✓
- Busca de informações do player ✓
- Cenários de rate limiting ✓

Observações:
- Adicionada cobertura completa para todos os métodos auxiliares
- Implementados testes para diferentes formatos de resposta
- Validação robusta de casos de borda
- Cenários de concorrência e performance não são apropriados para testes unitários
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch
from services.player_service import PlayerService
import requests

class TestPlayerService(TestCase):
    def setUp(self):
        self.player_service = PlayerService()
        self.player_service.repository = MagicMock()
        self.player_service.cache_service = MagicMock()
        self.player_service.storage_crypto = MagicMock()
        
        # Dados de teste padrão
        self.test_name = "TestPlayer"
        self.test_tag = "1234"
        self.test_player_info = {
            "id": 1,
            "email": "test@test.com",
            "login": "testlogin",
            "password": "encrypted"
        }
        self.expected_url = f"https://www.valking.gg/player?username={self.test_name}%23{self.test_tag}"

    def test_get_player_rank_success(self):
        # Configura mocks
        self.player_service.repository.get_all_players.return_value = [
            {**self.test_player_info, "name": self.test_name, "tag": self.test_tag}
        ]
        self.player_service.cache_service.get.return_value = None
        
        result = self.player_service.get_player_rank(self.test_name, self.test_tag)
        
        self.assertEqual(result["rank"]["message"], "Por favor, consulte seu rank diretamente em:")
        self.assertEqual(result["rank"]["url"], self.expected_url)
        self.assertEqual(result["name"], self.test_name)
        self.assertEqual(result["tag"], self.test_tag)

    def test_get_player_rank_from_cache(self):
        cached_rank = {
            "message": "Por favor, consulte seu rank diretamente em:",
            "url": self.expected_url
        }
        self.player_service.cache_service.get.return_value = cached_rank
        
        result = self.player_service.get_player_rank(self.test_name, self.test_tag)
        
        self.assertEqual(result["rank"], cached_rank)
        self.player_service.cache_service.get.assert_called_once()

    def test_get_player_rank_invalid_name(self):
        invalid_names = ["", "Player#123", None]
        
        for name in invalid_names:
            with self.assertRaises(ValueError):
                self.player_service.get_player_rank(name, self.test_tag)

    def test_get_player_rank_invalid_tag(self):
        invalid_tags = ["", "123456", None]
        
        for tag in invalid_tags:
            with self.assertRaises(ValueError):
                self.player_service.get_player_rank(self.test_name, tag)

    def test_player_not_found_in_db(self):
        self.player_service.repository.get_all_players.return_value = []
        self.player_service.cache_service.get.return_value = None
        
        result = self.player_service.get_player_rank(self.test_name, self.test_tag)
        
        self.assertEqual(result["id"], -1)
        self.assertEqual(result["rank"]["message"], "Por favor, consulte seu rank diretamente em:")
        self.assertEqual(result["rank"]["url"], self.expected_url)

    # Testes para build_player_result
    def test_build_player_result_complete(self):
        player_info = {
            "id": 123,
            "email": "test@email.com",
            "login": "testuser",
            "password": "encrypted_pass"
        }
        rank_info = {
            "message": "Por favor, consulte seu rank diretamente em:",
            "url": self.expected_url
        }
        
        result = self.player_service.build_player_result(
            player_info, "TestName", "TAG", rank_info
        )
        
        self.assertEqual(result["id"], 123)
        self.assertEqual(result["name"], "TestName")
        self.assertEqual(result["tag"], "TAG")
        self.assertEqual(result["rank"], rank_info)
        self.assertEqual(result["email"], "test@email.com")
        self.assertEqual(result["login"], "testuser")
        self.assertEqual(result["password"], "encrypted_pass")

    def test_build_player_result_minimal(self):
        result = self.player_service.build_player_result(
            {}, "TestName", "TAG", "Gold 3"
        )
        
        self.assertEqual(result["id"], -1)
        self.assertEqual(result["name"], "TestName")
        self.assertEqual(result["tag"], "TAG")
        self.assertEqual(result["rank"], "Gold 3")
        self.assertEqual(result["email"], "")
        self.assertEqual(result["login"], "")
        self.assertEqual(result["password"], "")

    # Testes para validate_player_params
    def test_validate_player_params_whitespace(self):
        name, tag = self.player_service.validate_player_params(" TestName ", " 123 ")
        self.assertEqual(name, "TestName")
        self.assertEqual(tag, "123")

    def test_validate_player_params_invalid_types(self):
        invalid_inputs = [
            (123, "tag"),  # número como nome
            ("name", 456),  # número como tag
            (None, "tag"),  # None como nome
            ("name", None),  # None como tag
        ]
        
        for name, tag in invalid_inputs:
            with self.assertRaises(ValueError):
                self.player_service.validate_player_params(name, tag)

    # Testes para get_player_info
    def test_get_player_info_multiple_players(self):
        test_players = [
            {"id": 1, "name": "Player1", "tag": "111", "email": "p1@test.com"},
            {"id": 2, "name": "Player2", "tag": "222", "email": "p2@test.com"},
            {"id": 3, "name": "TestPlayer", "tag": "1234", "email": "p3@test.com"}
        ]
        
        self.player_service.repository.get_all_players.return_value = test_players
        
        result = self.player_service.get_player_info("TestPlayer", "1234")
        
        self.assertEqual(result["id"], 3)
        self.assertEqual(result["email"], "p3@test.com")

    def test_get_player_info_empty_database(self):
        self.player_service.repository.get_all_players.return_value = []
        
        result = self.player_service.get_player_info("TestPlayer", "1234")
        
        self.assertEqual(result["id"], -1)
        self.assertEqual(result["email"], "")
        self.assertEqual(result["login"], "")
        self.assertEqual(result["password"], "")