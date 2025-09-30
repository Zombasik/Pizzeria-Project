"""
Настройка бота
"""
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from src.config import BOT_TOKEN, LOG_LEVEL, LOG_FILE
from src.handlers.admin import get_admin_router
from src.handlers.user import get_user_router


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )


def create_bot() -> Bot:
    """Создание экземпляра бота"""
    return Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_dispatcher() -> Dispatcher:
    """Создание диспетчера"""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Подключаем роутеры
    dp.include_router(get_admin_router())
    dp.include_router(get_user_router())

    return dp


async def setup_bot_commands(bot: Bot):
    """Настройка команд бота"""
    from aiogram.types import BotCommand

    commands = [
        BotCommand(command='start', description='Начало работы'),
        BotCommand(command='menu', description='Меню пиццерии'),
        BotCommand(command='admin', description='Админ-панель (только для админов)')
    ]

    await bot.set_my_commands(commands)