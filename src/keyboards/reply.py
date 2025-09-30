"""
Reply клавиатуры для пользователей
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Стартовая клавиатура
star_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍕 Меню")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="📋 Мои заказы")],
        [KeyboardButton(text="ℹ️ О нас"), KeyboardButton(text="📞 Контакты")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)

# Клавиатура для запроса контакта
contact_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Клавиатура для запроса локации
location_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Поделиться локацией", request_location=True)],
        [KeyboardButton(text="✍️ Ввести адрес вручную")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)