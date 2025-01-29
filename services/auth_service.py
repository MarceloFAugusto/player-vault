from services.crypto_service import CryptoService
import time
import logging

# Configuração do logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AuthService:
    def __init__(self):
        self.crypto_service = CryptoService()
        self.tokens = set()
        self.token_expiry = 60  # em segundos
        logger.info(
            "AuthService iniciado com tempo de expiração de %d segundos",
            self.token_expiry,
        )

    def get_expiry_time(self) -> int:
        return self.token_expiry

    def generate_token(self) -> str:
        timestamp = str(time.time())
        token = self.crypto_service.encrypt(timestamp)
        self.tokens.add(token)
        logger.info("Novo token gerado")
        return token

    def verify_token(self, token: str) -> bool:
        if not token:
            logger.warning("Token vazio recebido")
            return False

        if token not in self.tokens:
            logger.warning("Token não encontrado no conjunto de tokens válidos")
            return False

        try:
            timestamp = float(self.crypto_service.decrypt(token))
            if time.time() - timestamp > self.token_expiry:
                self.tokens.remove(token)
                logger.warning("Token expirado removido")
                return False
            logger.info("Token verificado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao decodificar o token: {str(e)}")
            return False


# Criando uma instância singleton do AuthService
auth_service = AuthService()
