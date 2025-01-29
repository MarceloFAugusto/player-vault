from services.crypto_service import CryptoService
from .base_repository import BaseRepository
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PlayerRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self.crypto_service = CryptoService()

    def get_all_players(self) -> List[Dict[str, Any]]:
        query = "SELECT id, name, tag, email, login FROM players"
        results = self.fetch_all(query)
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "tag": row["tag"],
                "email": row["email"],
                "login": row["login"]
            }
            for row in results
        ] if results else []

    def insert_player(
        self,
        player_data: Dict[str, str],
        encrypted_password: str,
    ) -> int:
        if not encrypted_password:
            logger.error("Senha criptografada não pode estar vazia")
            raise ValueError("Senha criptografada inválida")

        try:
            query = """
                INSERT INTO players (name, tag, email, login, password)
                VALUES (?, ?, ?, ?, ?)
            """
            cursor = self.execute_query(
                query,
                (
                    player_data["name"],
                    player_data["tag"],
                    player_data["email"].lower(),
                    player_data["login"],
                    encrypted_password,
                ),
            )
            player_id = cursor.lastrowid
            if not player_id:
                raise ValueError("Erro ao obter ID do jogador inserido")

            logger.info(f"Jogador inserido com ID: {player_id}")
            return player_id

        except Exception as e:
            logger.error(f"Erro ao inserir jogador: {str(e)}")
            if "UNIQUE constraint" in str(e):
                raise ValueError("Email ou login já existem no sistema")
            raise ValueError(f"Erro ao inserir jogador: {str(e)}")

    def insert_players(self, players_data) -> List[int]:
        try:
            with self.db_manager.get_cursor() as cursor:
                player_ids = []

                for player in players_data:
                    if not all(
                        key in player
                        for key in ["name", "tag", "email", "login", "password"]
                    ):
                        raise ValueError("Dados do jogador incompletos")

                    cursor.execute(
                        """
                        INSERT INTO players (name, tag, email, login, password)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            player["name"],
                            player["tag"],
                            player["email"].lower(),
                            player["login"],
                            player["password"],
                        ),
                    )
                    player_ids.append(cursor.lastrowid)

                logger.info(f"Jogadores inseridos com sucesso. IDs: {player_ids}")
                return player_ids

        except Exception as e:
            logger.error(f"Erro ao inserir jogadores: {str(e)}")
            if "UNIQUE constraint" in str(e):
                raise ValueError("Um ou mais emails/logins já existem no sistema")
            raise ValueError(f"Erro ao inserir jogadores: {str(e)}")

    def get_password_by_credentials(self, login: str, email: str) -> Optional[str]:
        query = """
            SELECT password
            FROM players
            WHERE LOWER(login) = ? AND LOWER(email) = ?
        """
        result = self.fetch_one(query, (login.lower(), email.lower()))
        return result[0] if result else None

    def delete_player(self, player_id: int) -> bool:
        query = "DELETE FROM players WHERE id = ?"
        cursor = self.execute_query(query, (player_id,))
        return cursor.rowcount > 0

    def check_player_exists(
        self,
        email: str = None,
        login: str = None,
    ) -> Dict[str, bool]:
        result = {"email_exists": False, "login_exists": False}

        try:
            if email:
                logger.debug(f"Verificando existência do email: {email}")
                query = "SELECT 1 FROM players WHERE LOWER(email) = ?"
                result["email_exists"] = bool(self.fetch_one(query, (email.lower(),)))
                logger.debug(f"Email {email} existe: {result['email_exists']}")

            if login:
                logger.debug(f"Verificando existência do login: {login}")
                query = "SELECT 1 FROM players WHERE LOWER(login) = ?"
                result["login_exists"] = bool(self.fetch_one(query, (login.lower(),)))
                logger.debug(f"Login {login} existe: {result['login_exists']}")

            logger.info(
                f"Verificação concluída - Email existe: {result['email_exists']}, "
                f"Login existe: {result['login_exists']}",
            )
            return result

        except Exception as e:
            logger.error(
                f"Erro ao verificar existência no banco - Email: {email}, "
                f"Login: {login}. Erro: {str(e)}",
            )
            raise ValueError(f"Erro na consulta ao banco de dados: {str(e)}")