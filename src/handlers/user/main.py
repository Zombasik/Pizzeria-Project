"""
Основные обработчики для пользователей
"""
import re
import os
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import ADMIN_IDS, RESTRICTED_WORDS
from src.keyboards.inline import (
    get_catalog_keyboard, get_cart_keyboard,
    get_main_menu_keyboard, get_confirm_order_keyboard
)
from src.services import UserService, ProductService, CartService
from src.bot.dependencies import get_db_session

router = Router()


class CatalogState(StatesGroup):
    """Состояния для работы с каталогом"""
    browsing = State()
    quantity_selection = State()


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
            "\n\n🔑 <b>Режим администратора</b>\n"
            "Используйте /admin для управления"
        )

    welcome_text = (
        f"🍕 <b>Добро пожаловать в Пиццерию!</b>\n\n"
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Мы рады видеть вас в нашем боте!\n"
        f"Здесь вы можете:\n\n"
        f"🔸 Просмотреть меню и выбрать любимую пиццу\n"
        f"🔸 Добавить товары в корзину\n"
        f"🔸 Оформить заказ с доставкой\n"
        f"🔸 Оплатить онлайн (если настроено)\n\n"
        f"📱 Наши контакты и информация о доставке\n"
        f"доступны в главном меню{admin_info}"
    )

    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())


@router.message(Command("menu"))
async def menu_command(message: types.Message, state: FSMContext):
    """Показать каталог товаров с фотографиями"""
    session = get_db_session()
    try:
        product_service = ProductService(session)
        products = product_service.get_all_products(available_only=True)

        if not products:
            await message.answer(
                "🍕 <b>МЕНЮ ПИЦЦЕРИИ</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                "😔 К сожалению, товары временно недоступны.\n\n"
                "Мы работаем над обновлением меню!\n"
                "Попробуйте зайти чуть позже.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        # Сохраняем список товаров в состояние
        await state.update_data(products=products, current_index=0, quantity=1)
        await state.set_state(CatalogState.browsing)

        # Показываем первый товар
        await show_product(message, products[0], 0, products, message.from_user.id)

    finally:
        session.close()


async def show_product(
    message: types.Message,
    product,
    index: int,
    products: list,
    user_id: int,
    edit: bool = False
):
    """Показать товар с фото и описанием"""
    caption = f"<b>{product.name}</b>\n\n"

    if product.description:
        caption += f"{product.description}\n\n"

    if product.category:
        caption += f"📍 Категория: {product.category}\n"

    caption += f"💰 Цена: <b>{product.price:.0f} руб.</b>"

    keyboard = get_catalog_keyboard(products, index, user_id)

    # Проверяем, есть ли фото
    if product.image:
        try:
            # Если это file_id от Telegram, используем его напрямую
            if product.image.startswith('AgAC') or product.image.startswith('BAA'):
                if edit:
                    media = InputMediaPhoto(media=product.image, caption=caption, parse_mode="HTML")
                    await message.edit_media(media=media, reply_markup=keyboard)
                else:
                    await message.answer_photo(
                        photo=product.image,
                        caption=caption,
                        reply_markup=keyboard
                    )
            # Если это локальный файл
            elif os.path.exists(product.image):
                photo = FSInputFile(product.image)
                if edit:
                    media = InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML")
                    await message.edit_media(media=media, reply_markup=keyboard)
                else:
                    await message.answer_photo(
                        photo=photo,
                        caption=caption,
                        reply_markup=keyboard
                    )
            else:
                raise FileNotFoundError("Image not found")
        except Exception as e:
            # Если ошибка с фото, отправляем текст
            text = f"🖼 <i>Фото временно недоступно</i>\n\n{caption}"
            if edit:
                await message.edit_text(text, reply_markup=keyboard)
            else:
                await message.answer(text, reply_markup=keyboard)
    else:
        # Если фото нет, отправляем текстовое сообщение
        text = f"🖼 <i>Фото отсутствует</i>\n\n{caption}"
        if edit:
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)


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
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋",
            reply_markup=get_main_menu_keyboard()
        )
    elif message.text.lower() in ["спасибо", "благодарю"]:
        await message.answer("Пожалуйста! 😊", reply_markup=get_main_menu_keyboard())
    else:
        # Стандартный ответ на неизвестные сообщения
        await message.answer(
            "🤔 Не понимаю. Используйте команду /start для начала работы."
        )