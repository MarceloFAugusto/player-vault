import time
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self, cache_duration: int = 300):  # 5 minutos por padrão
        self._cache = {}
        self.cache_duration = cache_duration

    def get(self, key: str) -> Optional[Any]:
        """Retorna o valor do cache se existir e não estiver expirado"""
        cached_data = self._cache.get(key)

        if cached_data:
            timestamp, value = cached_data
            if time.time() - timestamp < self.cache_duration:
                logger.info(f"Cache hit para {key}")
                return value
            else:
                # Cache expirado
                del self._cache[key]
                logger.info(f"Cache expirado para {key}")
        return None

    def set(self, key: str, value: Any):
        """Armazena um valor no cache"""
        self._cache[key] = (time.time(), value)
        logger.info(f"Cache atualizado para {key}")

    def clear(self):
        """Limpa todo o cache"""
        self._cache.clear()
        logger.info("Cache limpo")
