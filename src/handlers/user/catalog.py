"""
Обработчики для работы с каталогом и корзиной
"""
import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, FSInputFile

from src.services import ProductService, CartService
from src.keyboards.inline import (
    get_catalog_keyboard, get_cart_keyboard,
    get_main_menu_keyboard
)
from src.bot.dependencies import get_db_session

router = Router()


@router.callback_query(F.data.startswith("catalog_page:"))
async def catalog_navigation(callback: types.CallbackQuery, state: FSMContext):
    """Навигация по каталогу"""
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    products = data.get("products", [])

    if not products or page < 0 or page >= len(products):
        await callback.answer("Страница не найдена")
        return

    # Обновляем текущий индекс
    await state.update_data(current_index=page, quantity=1)

    # Показываем товар
    product = products[page]
    await show_product_edit(callback.message, product, page, products, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("qty_minus:") | F.data.startswith("qty_plus:"))
async def quantity_change(callback: types.CallbackQuery, state: FSMContext):
    """Изменение количества товара"""
    data = await state.get_data()
    current_qty = data.get("quantity", 1)

    if callback.data.startswith("qty_minus:"):
        new_qty = max(1, current_qty - 1)
    else:
        new_qty = min(10, current_qty + 1)

    await state.update_data(quantity=new_qty)

    # Обновляем кнопку количества
    products = data.get("products", [])
    current_index = data.get("current_index", 0)

    if products and 0 <= current_index < len(products):
        product = products[current_index]
        keyboard = get_catalog_keyboard_with_qty(
            products, current_index, callback.from_user.id, new_qty
        )
        await callback.message.edit_reply_markup(reply_markup=keyboard)

    await callback.answer(f"Количество: {new_qty}")


@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    """Добавить товар в корзину"""
    parts = callback.data.split(":")
    product_id = int(parts[1])

    data = await state.get_data()
    quantity = data.get("quantity", 1)

    session = get_db_session()
    try:
        cart_service = CartService(session)
        cart_service.add_to_cart(
            user_id=callback.from_user.id,
            product_id=product_id,
            quantity=quantity
        )

        # Сбрасываем количество
        await state.update_data(quantity=1)

        await callback.answer(
            f"✅ Добавлено в корзину ({quantity} шт.)",
            show_alert=True
        )

    finally:
        session.close()


@router.callback_query(F.data == "show_cart")
async def show_cart(callback: types.CallbackQuery):
    """Показать корзину"""
    session = get_db_session()
    try:
        cart_service = CartService(session)
        cart_items = cart_service.get_user_cart(callback.from_user.id)

        if not cart_items:
            await callback.message.edit_text(
                "🛒 <b>Ваша корзина пуста</b>\n\n"
                "Добавьте товары из каталога!",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            cart_text = "🛒 <b>ВАША КОРЗИНА</b>\n"
            cart_text += "━━━━━━━━━━━━━━━━━━━\n\n"

            total_price = 0
            for item in cart_items:
                cart_text += f"▫️ {item['product_name']}\n"
                cart_text += f"   {item['quantity']} x {item['product_price']:.0f} = "
                cart_text += f"<b>{item['total']:.0f} руб.</b>\n\n"
                total_price += item['total']

            cart_text += "━━━━━━━━━━━━━━━━━━━\n"
            cart_text += f"💰 <b>ИТОГО: {total_price:.0f} руб.</b>"

            keyboard = get_cart_keyboard(cart_items, total_price)
            await callback.message.edit_text(cart_text, reply_markup=keyboard)

        await callback.answer()

    finally:
        session.close()


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    """Очистить корзину"""
    session = get_db_session()
    try:
        cart_service = CartService(session)
        cart_service.clear_cart(callback.from_user.id)

        await callback.message.edit_text(
            "🗑 <b>Корзина очищена</b>\n\n"
            "Выберите товары из каталога!",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer("✅ Корзина очищена", show_alert=True)

    finally:
        session.close()


@router.callback_query(F.data == "back_to_catalog" | F.data == "show_catalog")
async def back_to_catalog(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к каталогу"""
    session = get_db_session()
    try:
        product_service = ProductService(session)
        products = product_service.get_all_products(available_only=True)

        if not products:
            await callback.message.edit_text(
                "🍕 <b>Каталог временно недоступен</b>\n\n"
                "Попробуйте позже!",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            # Сохраняем список товаров в состояние
            await state.update_data(products=products, current_index=0, quantity=1)

            # Показываем первый товар
            product = products[0]
            await show_product_edit(
                callback.message, product, 0, products, callback.from_user.id
            )

        await callback.answer()

    finally:
        session.close()


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    """Показать главное меню"""
    await callback.message.edit_text(
        "📋 <b>ГЛАВНОЕ МЕНЮ</b>\n\n"
        "Выберите раздел:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "show_contacts")
async def show_contacts(callback: types.CallbackQuery):
    """Показать контакты"""
    contacts_text = (
        "📞 <b>НАШИ КОНТАКТЫ</b>\n\n"
        "☎️ Телефон: +7 (999) 123-45-67\n"
        "📍 Адрес: г. Москва, ул. Примерная, д. 1\n"
        "⏰ Время работы: 10:00 - 22:00\n\n"
        "💬 Для заказа свяжитесь с нами!"
    )

    await callback.message.edit_text(
        contacts_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


async def show_product_edit(message, product, index, products, user_id):
    """Вспомогательная функция для показа товара с редактированием"""
    caption = f"<b>{product.name}</b>\n\n"

    if product.description:
        caption += f"{product.description}\n\n"

    if product.category:
        caption += f"📍 Категория: {product.category}\n"

    caption += f"💰 Цена: <b>{product.price:.0f} руб.</b>"

    keyboard = get_catalog_keyboard(products, index, user_id)

    # Проверяем, есть ли фото
    if product.image and os.path.exists(product.image):
        try:
            photo = FSInputFile(product.image)
            media = InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML")
            await message.edit_media(media=media, reply_markup=keyboard)
        except Exception:
            text = f"🖼 <i>Фото временно недоступно</i>\n\n{caption}"
            await message.edit_text(text, reply_markup=keyboard)
    else:
        text = f"🖼 <i>Фото отсутствует</i>\n\n{caption}"
        await message.edit_text(text, reply_markup=keyboard)


def get_catalog_keyboard_with_qty(products, current_index, user_id, quantity):
    """Создает клавиатуру с обновленным количеством"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    product = products[current_index]

    # Кнопки количества и добавления в корзину
    builder.row(
        types.InlineKeyboardButton(text="➖", callback_data=f"qty_minus:{product.id}"),
        types.InlineKeyboardButton(text=f"{quantity} шт", callback_data="qty_display"),
        types.InlineKeyboardButton(text="➕", callback_data=f"qty_plus:{product.id}")
    )

    # Кнопка добавления в корзину
    builder.row(
        types.InlineKeyboardButton(
            text="🛒 Добавить в корзину",
            callback_data=f"add_to_cart:{product.id}:{quantity}"
        )
    )

    # Навигация
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"catalog_page:{current_index - 1}"
            )
        )

    nav_buttons.append(
        types.InlineKeyboardButton(
            text=f"{current_index + 1}/{len(products)}",
            callback_data="page_info"
        )
    )

    if current_index < len(products) - 1:
        nav_buttons.append(
            types.InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"catalog_page:{current_index + 1}"
            )
        )

    builder.row(*nav_buttons)

    # Корзина и главное меню
    builder.row(
        types.InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart"),
        types.InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")
    )

    return builder.as_markup()