from .base_repository import BaseRepository
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GoogleAuthRepository(BaseRepository):
    def save_secret(self, user_id: int, secret: str):
        query = """
            INSERT INTO google_auth (user_id, secret_key, is_active)
            VALUES (?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET
            secret_key = excluded.secret_key,
            is_active = 0
        """
        self.execute_query(query, (user_id, secret))

    def activate_2fa(self, user_id: int, secret: str):
        query = """
            UPDATE google_auth
            SET is_active = 1,
                secret_key = ?
            WHERE user_id = ?
        """
        self.execute_query(query, (secret, user_id))

    def is_2fa_active(self, user_id: int) -> bool:
        query = "SELECT is_active FROM google_auth WHERE user_id = ?"
        result = self.fetch_one(query, (user_id,))
        return bool(result and result[0])

    def get_secret(self, user_id: int) -> Optional[str]:
        query = """
            SELECT secret_key
            FROM google_auth
            WHERE user_id = ? AND is_active = 1
        """
        result = self.fetch_one(query, (user_id,))
        return result[0] if result else None

    def delete_2fa(self, user_id: int):
        query = "DELETE FROM google_auth WHERE user_id = ?"
        self.execute_query(query, (user_id,))
