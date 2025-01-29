import sqlite3
import logging
import os
from contextlib import contextmanager
from threading import local
from config.settings import get_settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _local = local()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            settings = get_settings()
            cls._instance.DB_FILE_PATH = settings.DB_FILE_PATH
            logger.info(f"Inicializando DatabaseManager no ambiente: {settings.ENVIRONMENT}; DB: {cls._instance.DB_FILE_PATH}")
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            
            # Limpar banco de teste se existir
            settings = get_settings()
            
            if settings.TESTING:
                if os.path.exists(settings.DB_FILE_PATH):
                    os.remove(settings.DB_FILE_PATH)
                
            self.init_db()

    def init_db(self):
        """Inicializa o banco de dados e cria as tabelas"""
        try:
            with self.get_connection() as conn:
                # Tabela players
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS players (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        tag TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        login TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )
                """
                )

                # Tabela admin_users
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS admin_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL
                    )
                """
                )

                # Tabela google_auth
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS google_auth (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE,
                        secret_key TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES admin_users(id)
                    )
                """
                )

                # Índices
                conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON players(email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_login ON players(login)")

                conn.commit()
                logger.info("Banco de dados inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Gerencia a conexão com o banco de dados"""
        conn = None
        try:
            conn = sqlite3.connect(self.DB_FILE_PATH)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            logger.error(f"Erro na conexão com o banco: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Erro ao fechar conexão: {e}")

    @contextmanager
    def get_cursor(self):
        """Gerencia cursores com commit/rollback automático"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Erro na operação do banco: {e}")
                raise
            finally:
                cursor.close()


def get_db():
    """Função para obter uma instância do DatabaseManager"""
    return DatabaseManager()
