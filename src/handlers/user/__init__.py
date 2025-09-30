"""
Обработчики для пользователей
"""
from aiogram import Router
from .main import router as main_router


def get_user_router() -> Router:
    """Получить роутер для пользователей"""
    user_router = Router()
    user_router.include_router(main_router)
    return user_router