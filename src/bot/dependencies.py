"""
Зависимости для бота
"""
from sqlalchemy.orm import Session
from src.database.database import DatabaseManager
from src.config import DATABASE_URL

# Глобальный менеджер БД
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Получить менеджер базы данных"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(DATABASE_URL)
    return _db_manager


def get_db_session() -> Session:
    """Получить сессию базы данных"""
    return get_db_manager().get_session()