"""
Инлайн-клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from src.database.models import Product


def get_catalog_keyboard(
    products: List[Product],
    current_index: int = 0,
    user_id: int = None
) -> InlineKeyboardMarkup:
    """
    Создает инлайн-клавиатуру для каталога товаров
    """
    builder = InlineKeyboardBuilder()

    if not products:
        return builder.as_markup()

    product = products[current_index]

    # Кнопки количества и добавления в корзину
    builder.row(
        InlineKeyboardButton(text="➖", callback_data=f"qty_minus:{product.id}"),
        InlineKeyboardButton(text="1 шт", callback_data="qty_display"),
        InlineKeyboardButton(text="➕", callback_data=f"qty_plus:{product.id}")
    )

    # Кнопка добавления в корзину
    builder.row(
        InlineKeyboardButton(
            text="🛒 Добавить в корзину",
            callback_data=f"add_to_cart:{product.id}:1"
        )
    )

    # Навигация по каталогу
    nav_buttons = []

    # Кнопка "Назад"
    if current_index > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"catalog_page:{current_index - 1}"
            )
        )

    # Счетчик страниц
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_index + 1}/{len(products)}",
            callback_data="page_info"
        )
    )

    # Кнопка "Вперед"
    if current_index < len(products) - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"catalog_page:{current_index + 1}"
            )
        )

    builder.row(*nav_buttons)

    # Кнопки корзины и главного меню
    builder.row(
        InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart"),
        InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")
    )

    return builder.as_markup()


def get_cart_keyboard(cart_items: List, total_price: float) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для корзины
    """
    builder = InlineKeyboardBuilder()

    if cart_items:
        # Кнопка оформления заказа
        builder.row(
            InlineKeyboardButton(
                text=f"✅ Оформить заказ ({total_price:.0f} руб.)",
                callback_data="checkout"
            )
        )

        # Кнопка очистки корзины
        builder.row(
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data="clear_cart"
            )
        )

    # Кнопка возврата к каталогу
    builder.row(
        InlineKeyboardButton(
            text="🔙 Вернуться к меню",
            callback_data="back_to_catalog"
        )
    )

    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру главного меню
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🍕 Каталог товаров", callback_data="show_catalog")
    )

    builder.row(
        InlineKeyboardButton(text="🛒 Моя корзина", callback_data="show_cart")
    )

    builder.row(
        InlineKeyboardButton(text="📞 Контакты", callback_data="show_contacts")
    )

    return builder.as_markup()


def get_confirm_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру подтверждения заказа
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data=f"confirm_order:{order_id}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить заказ",
            callback_data=f"cancel_order:{order_id}"
        )
    )

    return builder.as_markup()