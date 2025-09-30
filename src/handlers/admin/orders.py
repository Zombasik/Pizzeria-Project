"""
Обработчики админ-панели для управления заказами
"""
from aiogram import Router, F, types

from src.config import ADMIN_IDS
from src.keyboards.admin import admin_kb
from src.services import OrderService
from src.bot.dependencies import get_db_session

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


@router.callback_query(F.data == "admin_orders")
async def orders_menu_handler(callback: types.CallbackQuery):
    """Меню управления заказами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📋 <b>Управление заказами</b>\n\n"
        "Выберите статус заказов для просмотра:",
        reply_markup=admin_kb.orders_menu()
    )


@router.callback_query(F.data.startswith("orders_"))
async def orders_list_handler(callback: types.CallbackQuery):
    """Список заказов по статусу"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    status = callback.data.split("_")[1]

    status_map = {
        "new": "pending",
        "processing": "processing",
        "completed": "completed",
        "cancelled": "cancelled"
    }

    status_text = {
        "new": "🆕 Новые заказы",
        "processing": "🔄 В обработке",
        "completed": "✅ Выполненные",
        "cancelled": "❌ Отмененные"
    }

    session = get_db_session()
    try:
        order_service = OrderService(session)
        orders = order_service.get_orders_by_status(status_map.get(status, "pending"))

        if not orders:
            await callback.message.edit_text(
                f"{status_text[status]}\n\n"
                "Заказов с таким статусом нет.",
                reply_markup=admin_kb.orders_menu()
            )
            return

        text = f"{status_text[status]}:\n\n"

        for order in orders[:5]:  # Показываем только 5 последних
            text += f"🆔 Заказ #{order.id}\n"
            text += f"👤 {order.username or 'Без имени'}\n"
            text += f"📱 {order.phone or 'Нет телефона'}\n"
            text += f"💰 {order.total_price} руб.\n"
            text += f"🕐 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"/order_{order.id}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=admin_kb.orders_menu()
        )
    finally:
        session.close()


@router.message(F.text.regexp(r'^/order_(\d+)$'))
async def order_detail_handler(message: types.Message):
    """Детали конкретного заказа"""
    if not is_admin(message.from_user.id):
        return

    order_id = int(message.text.split('_')[1])

    session = get_db_session()
    try:
        order_service = OrderService(session)
        order_details = order_service.get_order_details(order_id)

        if not order_details:
            await message.answer("❌ Заказ не найден")
            return

        order = order_details['order']
        items = order_details['items']

        text = (
            f"📋 <b>Заказ #{order.id}</b>\n\n"
            f"👤 Клиент: {order.username or 'Без имени'}\n"
            f"📱 Телефон: {order.phone or 'Не указан'}\n"
            f"📍 Адрес: {order.address or 'Не указан'}\n"
            f"🕐 Время: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📊 Статус: {order.status}\n\n"
            f"<b>Состав заказа:</b>\n"
        )

        for item in items:
            text += (
                f"• {item['product'].name} x{item['quantity']} "
                f"= {item['total']} руб.\n"
            )

        text += f"\n💰 <b>Итого: {order.total_price} руб.</b>"

        await message.answer(
            text,
            reply_markup=admin_kb.order_actions(order_id)
        )
    finally:
        session.close()


@router.callback_query(F.data.startswith("order_"))
async def order_action_handler(callback: types.CallbackQuery):
    """Обработка действий с заказами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    action, order_id = callback.data.split(":")
    order_id = int(order_id)

    status_map = {
        "order_accept": "processing",
        "order_cancel": "cancelled",
        "order_delivering": "delivering",
        "order_complete": "completed"
    }

    status_text = {
        "order_accept": "принят в обработку",
        "order_cancel": "отменен",
        "order_delivering": "передан в доставку",
        "order_complete": "завершен"
    }

    new_status = status_map.get(action)
    if not new_status:
        await callback.answer("❌ Неизвестное действие")
        return

    session = get_db_session()
    try:
        order_service = OrderService(session)
        success = order_service.update_order_status(order_id, new_status)

        if success:
            await callback.answer(
                f"✅ Заказ #{order_id} {status_text[action]}",
                show_alert=True
            )
            await callback.message.edit_reply_markup(
                reply_markup=admin_kb.orders_menu()
            )
        else:
            await callback.answer("❌ Ошибка обновления заказа", show_alert=True)
    finally:
        session.close()