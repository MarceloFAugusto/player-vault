from .base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class AdminRepository(BaseRepository):
    def verify_admin(self, username: str, password: str) -> bool:
        query = """
            SELECT id FROM admin_users
            WHERE username = ? AND password = ?
        """
        result = self.fetch_one(query, (username, password))
        return result is not None
