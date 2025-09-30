"""
Модуль бота
"""
from .setup import setup_logging, create_bot, create_dispatcher, setup_bot_commands
from .dependencies import get_db_manager, get_db_session