from database.admin_repository import AdminRepository
import logging

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self):
        self.repository = AdminRepository()

    def verify_admin(self, username: str, password: str) -> bool:
        try:
            result = self.repository.verify_admin(username, password)
            if result:
                logger.info(f"Admin {username} verificado com sucesso.")
            else:
                logger.warning(f"Falha na verificação do admin: {username}")
            return result
        except Exception as e:
            logger.error(f"Erro ao verificar admin: {e}")
            return False
