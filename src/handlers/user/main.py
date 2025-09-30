"""
Основные обработчики для пользователей
"""
import re
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command

from src.config import ADMIN_IDS, RESTRICTED_WORDS
from src.keyboards.reply import star_kb
from src.services import UserService
from src.bot.dependencies import get_db_session

router = Router()


@router.message(CommandStart())
async def start_command(message: types.Message):
    """Обработка команды /start"""
    user_id = message.from_user.id

    # Сохраняем пользователя в БД
    session = get_db_session()
    try:
        user_service = UserService(session)
        user_data = {
            'user_id': user_id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name
        }
        user_service.get_or_create_user(user_data)
    finally:
        session.close()

    # Информация для администраторов
    admin_info = ""
    if user_id in ADMIN_IDS:
        admin_info = (
            "\n\n🔑 Вы администратор! "
            "Используйте /admin для входа в панель управления."
        )

    await message.answer(
        f"👋 Добро пожаловать в Pizza Bot!\n"
        f"Ваш Telegram ID: <code>{user_id}</code>{admin_info}",
        reply_markup=star_kb
    )


@router.message(Command("menu"))
@router.message(F.text.lower() == "🍕 меню")
async def menu_command(message: types.Message):
    """Показать меню пиццерии"""
    await message.answer(
        "🍕 <b>Меню нашей пиццерии</b>\n\n"
        "Скоро здесь будет список наших вкусных пицц!",
        reply_markup=star_kb
    )


@router.message(F.text.lower() == "время")
async def time_command(message: types.Message):
    """Показать текущее время"""
    current_time = datetime.now().strftime("%H:%M:%S")
    await message.reply(f"Сейчас {current_time}")


@router.message(F.text)
async def text_filter(message: types.Message):
    """Фильтр запрещенных слов"""
    # Проверяем на запрещенные слова
    words = re.findall(r'\b\w+\b', message.text.lower())
    if RESTRICTED_WORDS.intersection(words):
        await message.delete()
        await message.answer(
            f"{message.from_user.first_name}, "
            f"вы не можете использовать эти слова!"
        )
        return

    # Обработка других текстовых сообщений
    if message.text.lower() in ["привет", "hello", "hi"]:
        await message.answer(f"Привет, {message.from_user.first_name}! 👋")
    elif message.text.lower() in ["спасибо", "благодарю"]:
        await message.answer("Пожалуйста! 😊")
    else:
        # Стандартный ответ на неизвестные сообщения
        await message.answer(
            "🤔 Не понимаю. Используйте кнопки меню для навигации.",
            reply_markup=star_kb
        )