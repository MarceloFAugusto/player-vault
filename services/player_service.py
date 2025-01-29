from database.player_repository import PlayerRepository
from services.crypto_service import CryptoService
from services.cache_service import CacheService
from typing import Dict, List, Optional, Any
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PlayerService:
    def __init__(self):
        self.repository = PlayerRepository()
        self.storage_crypto = CryptoService(key="valorant-players-ranks-v1")
        self.cache_service = CacheService(cache_duration=300)

    def get_player_rank(self, name: str, tag: str) -> Dict[str, Any]:
        try:
            logger.info(f"Iniciando busca de rank para jogador: {name}#{tag}")
            
            name, tag = self.validate_player_params(name, tag)
            player_info = self.get_player_info(name, tag)
            
            cache_key = f"{name}#{tag}"
            cached_rank = self.get_cached_rank(cache_key)
            
            if cached_rank:
                logger.info(f"Rank encontrado no cache: {cached_rank}")
                return self.build_player_result(player_info, name, tag, cached_rank)

            try:
                rank = self.fetch_rank_online(name, tag)
                self.cache_service.set(cache_key, rank)
            except requests.exceptions.Timeout:
                logger.error("Timeout na requisição")
                raise ValueError("Erro ao buscar rank: Timeout na requisição")

            result = self.build_player_result(player_info, name, tag, rank)
            logger.info(f"Retornando resultado final: {result}")
            return result

        except Exception as e:
            logger.error(f"Erro ao buscar rank: {str(e)}")
            logger.error(f"Tipo do erro: {type(e)}")
            logger.error(f"Local do erro:", exc_info=True)
            raise ValueError(f"Erro ao buscar rank: {str(e)}")

    def validate_player_params(self, name: str, tag: str) -> tuple[str, str]:
        if not isinstance(name, str) or not isinstance(tag, str):
            raise ValueError("Nome e tag devem ser strings")
        
        if name is None or tag is None:
            raise ValueError("Nome e tag não podem ser None")
        
        name = str(name).strip()
        tag = str(tag).strip()
        
        if not name or '#' in name:
            raise ValueError("Nome em formato inválido")
        if not tag or len(tag) > 5:
            raise ValueError("Tag em formato inválido")
            
        return name, tag

    def get_player_info(self, name: str, tag: str) -> Dict[str, Any]:
        player_info = {"id": -1, "email": "", "login": "", "password": ""}
        
        logger.debug("Buscando jogador no banco de dados")
        players = self.repository.get_all_players()
        logger.debug(f"Players encontrados: {len(players) if players else 0}")

        if players:
            player_info = next(
                (p for p in players if p["name"] == name and p["tag"] == tag),
                player_info
            )
            logger.debug(f"Player info encontrado: {player_info}")
            
        return player_info

    def get_cached_rank(self, cache_key: str) -> Optional[str]:
        logger.debug(f"Verificando cache com chave: {cache_key}")
        return self.cache_service.get(cache_key)

    def fetch_rank_online(self, name: str, tag: str) -> str:
        url = f"https://www.valking.gg/player?username={name}%23{tag}"
            
        logger.info("Redirecionando usuário para consulta direta no Valking.gg")
        return {
            "message": "Por favor, consulte seu rank diretamente em:",
            "url": url
        }

    def build_player_result(self, player_info: Dict[str, Any], name: str, tag: str, rank: str) -> Dict[str, Any]:
        return {
            "id": player_info.get("id", -1),
            "name": name,
            "tag": tag,
            "rank": rank,
            "email": player_info.get("email", ""),
            "login": player_info.get("login", ""),
            "password": player_info.get("password", ""),
        }

    def add_player(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            existing = self.check_player_exists(player_data["email"], player_data["login"])
            
            if existing["email_exists"]:
                raise ValueError("Email já cadastrado")
            
            if existing["login_exists"]:
                raise ValueError("Login já cadastrado")

            encrypted_password = self.storage_crypto.encrypt(player_data["password"])
            
            player_with_encrypted = player_data.copy()
            player_with_encrypted["password"] = encrypted_password
            
            player_id = self.repository.insert_player(
                player_data=player_with_encrypted,
                encrypted_password=encrypted_password
            )
            
            return {
                "id": player_id,
                "name": player_data["name"],
                "tag": player_data["tag"],
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Erro ao adicionar jogador: {str(e)}")
            raise

    def add_players(self, players_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        processed_players = []
        for player in players_data:
            storage_encrypted_password = self.storage_crypto.encrypt(player["password"])
            processed_players.append({**player, "password": storage_encrypted_password})

        try:
            player_ids = self.repository.insert_players(processed_players)
            logger.info(f"{len(players_data)} jogadores inseridos com sucesso.")

            return [
                {"id": pid, "name": player["name"], "tag": player["tag"]}
                for pid, player in zip(player_ids, players_data)
            ]
        except Exception as e:
            logger.error(f"Erro ao inserir jogadores em lote: {e}")
            raise ValueError(str(e))

    def verify_credentials(self, login: str, email: str) -> Optional[Dict[str, str]]:
        encrypted_password = self.repository.get_password_by_credentials(login, email)

        if encrypted_password:
            logger.info(f"Credenciais verificadas para o login: {login}")
            return {"password": self.storage_crypto.decrypt(encrypted_password)}

        logger.warning(f"Falha na verificação de credenciais para o login: {login}")
        return None

    def get_all_players(self) -> List[Dict[str, Any]]:
        try:
            players = self.repository.get_all_players()
            return [
                {"id": p["id"], "name": p["name"], "tag": p["tag"]}
                for p in players
            ]
        except Exception as e:
            logger.error(f"Erro ao buscar jogadores: {str(e)}")
            raise

    def delete_player(self, player_id: int) -> Dict[str, str]:
        try:
            if self.repository.delete_player(player_id):
                return {
                    "status": "success",
                    "message": "Jogador deletado com sucesso"
                }
            return {
                "status": "error",
                "message": "Jogador não encontrado"
            }
        except Exception as e:
            logger.error(f"Erro ao deletar jogador: {str(e)}")
            raise

    def check_player_exists(self, email: str = None, login: str = None) -> Dict[str, bool]:
        try:
            logger.info(
                f"Iniciando verificação de existência - Email: {email}, Login: {login}"
            )

            if not email and not login:
                logger.warning("Nenhum parâmetro fornecido para verificação")
                return {"email_exists": False, "login_exists": False}

            result = self.repository.check_player_exists(email, login)

            logger.info(
                f"Verificação concluída - Email existe: {result.get('email_exists')}, "
                f"Login existe: {result.get('login_exists')}"
            )
            return result

        except Exception as e:
            logger.error(
                f"Erro ao verificar existência do jogador - Email: {email}, "
                f"Login: {login}. Erro: {str(e)}"
            )
            raise ValueError(f"Erro ao verificar jogador: {str(e)}")