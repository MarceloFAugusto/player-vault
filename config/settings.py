import os
from functools import lru_cache
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = False
    TESTING: bool = False
    DB_FILE_PATH: str = ".\\database\\valorant.db"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 4
    CORS_ORIGINS: list = ["http://localhost:8000"]
    LOG_LEVEL: str = "DEBUG"
    TEST_2FA_SECRET: str = ""
    ADMIN_USER: str = ""
    ADMIN_PASS: str = ""
    
class TestSettings(Settings):
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    TESTING: bool = True
    DB_FILE_PATH: str = ".\\database\\test_valorant.db"
    WORKERS: int = 1
    LOG_LEVEL: str = "WARNING"
    TEST_2FA_SECRET: str = ""
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "admin"
    
@lru_cache()
def get_settings():
    environment = os.getenv("ENVIRONMENT", "production")
    print(f"Environment: {environment}")
    if environment == "test":
        return TestSettings()
    return Settings()
