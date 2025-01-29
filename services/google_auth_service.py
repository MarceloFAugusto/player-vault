import pyotp
from typing import Optional, Dict
from database.google_auth_repository import GoogleAuthRepository
import logging

logger = logging.getLogger(__name__)


class GoogleAuthService:
    def __init__(self):
        self.repository = GoogleAuthRepository()

    def generate_secret(self) -> str:
        return pyotp.random_base32()

    def get_qr_url(self, username: str, secret: str) -> str:
        totp = pyotp.totp.TOTP(secret)
        return totp.provisioning_uri(
            name=username, issuer_name="ValorantAccounts"
        ).replace(
            " ", "%20"
        )  # Garantir que a URL esteja codificada corretamente

    def verify_code(self, secret: str, code: str) -> bool:
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code)
        except Exception as e:
            logger.error(f"Erro ao verificar código: {e}")
            return False

    def activate_2fa(self, user_id: int, secret: str) -> bool:
        try:
            self.repository.activate_2fa(user_id, secret)
            logger.info(f"2FA ativado para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao ativar 2FA: {e}")
            return False

    def is_2fa_active(self, user_id: int) -> bool:
        try:
            secret = self.repository.get_secret(user_id)
            return secret is not None and len(secret) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar status do 2FA: {e}")
            return False

    def check_2fa_status(self, user_id: int) -> Dict[str, any]:
        """Verifica o status do 2FA e retorna novo segredo apenas se necessário"""
        try:
            is_configured = self.is_2fa_active(user_id)
            response = {"is_configured": is_configured}

            if not is_configured:
                secret = self.generate_secret()
                self.repository.save_secret(user_id, secret)
                response.update(
                    {"secret": secret, "qr_code_url": None}  # URL será gerada no router
                )

            return response
        except Exception as e:
            logger.error(f"Erro ao verificar status do 2FA: {e}")
            raise Exception(str(e))

    def setup_2fa(self, user_id: int) -> Dict[str, any]:
        """Substituir método antigo por chamada ao check_2fa_status"""
        return self.check_2fa_status(user_id)

    def get_user_secret(self, user_id: int) -> Optional[str]:
        try:
            return self.repository.get_secret(user_id)
        except Exception as e:
            logger.error(f"Erro ao buscar segredo do usuário: {e}")
            return None

    def reset_2fa(self, user_id: int) -> bool:
        try:
            self.repository.delete_2fa(user_id)
            logger.info(f"2FA resetado para usuário {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao resetar 2FA: {e}")
            raise Exception("Erro ao resetar 2FA")
