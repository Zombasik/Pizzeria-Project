"""
Главные обработчики админ-панели
"""
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import func

from src.config import ADMIN_IDS
from src.keyboards.admin import admin_kb
from src.database.models import TelegramUser, Product, Order
from src.bot.dependencies import get_db_session

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


@router.message(Command('admin'))
async def admin_main_menu(message: types.Message):
    """Главное меню админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return

    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=admin_kb.main_menu()
    )


@router.callback_query(F.data == "admin_back")
async def admin_back_handler(callback: types.CallbackQuery):
    """Возврат в главное меню админки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🔧 <b>Панель администратора</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=admin_kb.main_menu()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: types.CallbackQuery):
    """Статистика бота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    session = get_db_session()
    try:
        # Подсчет статистики
        total_users = session.query(func.count(TelegramUser.id)).scalar()
        total_products = session.query(func.count(Product.id)).scalar()
        total_orders = session.query(func.count(Order.id)).scalar()

        # Подсчет заказов по статусам
        pending_orders = session.query(func.count(Order.id)).filter_by(
            status='pending'
        ).scalar()
        completed_orders = session.query(func.count(Order.id)).filter_by(
            status='completed'
        ).scalar()

        # Общая сумма продаж
        total_sales = session.query(func.sum(Order.total_price)).filter_by(
            status='completed'
        ).scalar() or 0

        text = (
            "📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"📦 Всего товаров: {total_products}\n"
            f"📋 Всего заказов: {total_orders}\n\n"
            f"🆕 Новых заказов: {pending_orders}\n"
            f"✅ Выполнено заказов: {completed_orders}\n\n"
            f"💰 Общая сумма продаж: {total_sales:.2f} руб."
        )

        await callback.message.edit_text(
            text,
            reply_markup=admin_kb.main_menu()
        )
    finally:
        session.close()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    """Отмена текущего действия"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=admin_kb.main_menu()
    )


@router.callback_query(F.data == "admin_close")
async def close_admin_handler(callback: types.CallbackQuery):
    """Закрытие админ-панели"""
    await callback.message.delete()
    await callback.answer("Панель закрыта")