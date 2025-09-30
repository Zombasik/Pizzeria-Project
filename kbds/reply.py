from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


star_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Меню"),
            KeyboardButton(text="О магазине"),
        ],
        [
            KeyboardButton(text="Варианты доствки"),
            KeyboardButton(text="Варианты оплаты"),
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder='Что Вас интересует?'
)