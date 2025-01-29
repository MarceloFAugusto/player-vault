from typing import Any, List, Tuple, Optional
import logging
from database.db_manager import get_db

logger = logging.getLogger(__name__)


class BaseRepository:
    def __init__(self):
        self.db_manager = get_db()

    def execute_query(self, query: str, params: Tuple = None) -> Any:
        with self.db_manager.get_cursor() as cursor:
            try:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                return cursor
            except Exception as e:
                logger.error(f"Erro ao executar query: {str(e)}")
                raise

    def fetch_one(self, query: str, params: Tuple = None) -> Optional[Any]:
        with self.db_manager.get_cursor() as cursor:
            try:
                cursor.execute(query, params or ())
                return cursor.fetchone()
            except Exception as e:
                logger.error(f"Erro ao buscar registro: {str(e)}")
                raise

    def fetch_all(self, query: str, params: Tuple = None) -> List[Any]:
        with self.db_manager.get_cursor() as cursor:
            try:
                cursor.execute(query, params or ())
                return cursor.fetchall()
            except Exception as e:
                logger.error(f"Erro ao buscar registros: {str(e)}")
                raise

    def execute_transaction(self, queries: List[Tuple[str, Tuple]]) -> List[Any]:
        with self.db_manager.get_cursor() as cursor:
            results = []
            try:
                for query, params in queries:
                    cursor.execute(query, params or ())
                    if query.strip().upper().startswith("SELECT"):
                        results.append(cursor.fetchall())
                    else:
                        results.append(cursor.lastrowid)
                return results
            except Exception as e:
                logger.error(f"Erro na transação: {str(e)}")
                raise
