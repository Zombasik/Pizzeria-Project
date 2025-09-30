"""
Обработчики админ-панели
"""
from aiogram import Router
from .main import router as main_router
from .products import router as products_router
from .orders import router as orders_router


def get_admin_router() -> Router:
    """Получить роутер для админ-панели"""
    admin_router = Router()

    admin_router.include_router(main_router)
    admin_router.include_router(products_router)
    admin_router.include_router(orders_router)

    return admin_router