from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import logging

logger = logging.getLogger(__name__)


class CryptoService:
    def __init__(self, key="valorant-ranks-v1"):
        logger.debug("Inicializando CryptoService")
        try:
            self.key = self._derive_key(key.encode())
            self.aesgcm = AESGCM(self.key)
            logger.info("CryptoService inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar CryptoService: {str(e)}")
            raise

    def _derive_key(self, key_material):
        logger.debug("Derivando chave criptográfica")
        salt = b"valorant-static-salt"  # Mesmo salt do frontend
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return kdf.derive(key_material)
        except Exception as e:
            logger.error(f"Erro ao derivar chave: {str(e)}")
            raise

    def encrypt(self, data: str) -> str:
        if not isinstance(data, str) or not data:
            logger.error("Dados inválidos para criptografia")
            raise ValueError("Dados inválidos para criptografia")

        try:
            iv = os.urandom(12)
            data_bytes = data.encode("utf-8")
            encrypted = self.aesgcm.encrypt(iv, data_bytes, None)

            # Combina IV + dados criptografados
            combined = iv + encrypted
            return base64.b64encode(combined).decode("utf-8")
        except Exception as e:
            logger.error(f"Erro na criptografia: {str(e)}")
            raise ValueError(f"Erro na criptografia: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        if not isinstance(encrypted_data, str) or not encrypted_data:
            logger.error("Dados inválidos para descriptografia")
            raise ValueError("Dados inválidos para descriptografia")

        try:
            # Decodifica base64
            decoded = base64.b64decode(encrypted_data)
            if len(decoded) <= 12:
                raise ValueError("Dados criptografados inválidos")

            # Separa IV e dados criptografados
            iv = decoded[:12]
            ciphertext = decoded[12:]

            # Descriptografa
            decrypted = self.aesgcm.decrypt(iv, ciphertext, None)
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Erro na descriptografia: {str(e)}")
            raise ValueError(f"Erro na descriptografia: {str(e)}")
