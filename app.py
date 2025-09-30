import asyncio
import re
import secrets
from datetime import datetime, timedelta
from aiogram import F, Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from kbds import reply, admin_kb
from database.models import Base, TelegramUser, AdminToken, Product, Order, OrderItem, Cart
from config import BOT_TOKEN, ADMIN_IDS, DATABASE_URL, ADMIN_URL, TOKEN_LIFETIME_HOURS, RESTRICTED_WORDS

# Настройка базы данных
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)



bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# FSM состояния для админки
class ProductStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_image = State()
    waiting_for_edit_field = State()
    waiting_for_edit_value = State()

class OrderStates(StatesGroup):
    waiting_for_status_change = State()

class UserStates(StatesGroup):
    waiting_for_user_action = State()

# Инициализация с хранилищем состояний
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


@dp.message(Command('start'))
async def start_cmd(message: types.Message):
    user_id = message.from_user.id

    # Показываем ID пользователя для удобства настройки админов
    admin_info = ""
    if user_id in ADMIN_IDS:
        admin_info = "\n\n🔑 Вы администратор! Используйте /admin для входа в панель управления."

    await message.answer(
        f"👋 Добро пожаловать в Pizza Bot!\n"
        f"Ваш Telegram ID: <code>{user_id}</code>{admin_info}",
        reply_markup=reply.star_kb,
        parse_mode=ParseMode.HTML
    )


# Обработка главного меню админки
@dp.callback_query(F.data == "admin_back")
async def admin_main_menu_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🔧 <b>Панель администратора</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=admin_kb.admin_main_menu
    )

# === УПРАВЛЕНИЕ ТОВАРАМИ ===

@dp.callback_query(F.data == "admin_products")
async def products_menu_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📦 <b>Управление товарами</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_kb.products_menu
    )

@dp.callback_query(F.data == "product_list")
async def product_list_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    session = Session()
    try:
        products = session.query(Product).all()

        if not products:
            await callback.message.edit_text(
                "📦 Товаров пока нет.\n"
                "Добавьте первый товар!",
                reply_markup=admin_kb.products_menu
            )
            return

        text = "📦 <b>Список товаров:</b>\n\n"

        for product in products:
            status = "✅" if product.available else "❌"
            text += f"{status} <b>{product.name}</b>\n"
            text += f"   💰 {product.price} руб.\n"
            text += f"   📂 {product.category or 'Без категории'}\n"
            text += f"   /product_{product.id}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=admin_kb.products_menu
        )
    finally:
        session.close()

@dp.callback_query(F.data == "product_add")
async def product_add_handler(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await state.set_state(ProductStates.waiting_for_name)
    await callback.message.edit_text(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Шаг 1/5: Введите название товара:",
        reply_markup=admin_kb.cancel_kb
    )

@dp.message(ProductStates.waiting_for_name)
async def product_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProductStates.waiting_for_description)

    await message.answer(
        "Шаг 2/5: Введите описание товара:",
        reply_markup=admin_kb.cancel_kb
    )

@dp.message(ProductStates.waiting_for_description)
async def product_description_handler(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(ProductStates.waiting_for_price)

    await message.answer(
        "Шаг 3/5: Введите цену товара (только число):",
        reply_markup=admin_kb.cancel_kb
    )

@dp.message(ProductStates.waiting_for_price)
async def product_price_handler(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(ProductStates.waiting_for_category)

        await message.answer(
            "Шаг 4/5: Введите категорию товара (например: Пицца, Напитки, Десерты):",
            reply_markup=admin_kb.cancel_kb
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число!")

@dp.message(ProductStates.waiting_for_category)
async def product_category_handler(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(ProductStates.waiting_for_image)

    await message.answer(
        "Шаг 5/5: Отправьте фото товара или введите 'пропустить':",
        reply_markup=admin_kb.cancel_kb
    )

@dp.message(ProductStates.waiting_for_image)
async def product_image_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()

    image_path = None
    if message.photo:
        # Сохраняем ID фото
        image_path = message.photo[-1].file_id
    elif message.text.lower() != 'пропустить':
        await message.answer("❌ Отправьте фото или введите 'пропустить'")
        return

    # Сохраняем товар в БД
    session = Session()
    try:
        product = Product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category=data['category'],
            image=image_path,
            available=True
        )
        session.add(product)
        session.commit()

        await message.answer(
            f"✅ Товар '<b>{data['name']}</b>' успешно добавлен!\n\n"
            f"💰 Цена: {data['price']} руб.\n"
            f"📂 Категория: {data['category']}",
            reply_markup=admin_kb.products_menu
        )
    except Exception as e:
        session.rollback()
        await message.answer(f"❌ Ошибка при добавлении товара: {str(e)}")
    finally:
        session.close()
        await state.clear()

@dp.message(or_f(Command("menu"), (F.text.lower() == "меню")))
async def menu_cmd(message: types.Message):
    await message.answer("Это кнопка меню")
  #  await message.reply(message.text) 


restricted_words = RESTRICTED_WORDS

@dp.message(F.text.lower() == "время")
async def echo_cmd(message: types.Message):
    await message.reply("Сейчас " + datetime.now().strftime("%H:%M:%S"))


# Проверка прав администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Команда /admin - главное меню админки в Telegram
@dp.message(Command('admin'))
async def admin_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return

    await message.answer(
        "🔧 <b>Панель администратора</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=admin_kb.admin_main_menu
    )


@dp.message(Command('setadmin'))
async def set_admin_cmd(message: types.Message):
    user_id = message.from_user.id

    # Проверяем, является ли пользователь главным администратором (первый в списке)
    if user_id != ADMIN_IDS[0]:
        await message.answer("❌ Только главный администратор может добавлять других админов!")
        return

    # Получаем ID нового администратора из сообщения
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("Использование: /setadmin <user_id>")
            return

        new_admin_id = int(parts[1])

        if new_admin_id not in ADMIN_IDS:
            ADMIN_IDS.append(new_admin_id)
            await message.answer(f"✅ Пользователь {new_admin_id} добавлен в администраторы")
        else:
            await message.answer("Этот пользователь уже является администратором")
    except ValueError:
        await message.answer("❌ Неверный ID пользователя")


# === УПРАВЛЕНИЕ ЗАКАЗАМИ ===

@dp.callback_query(F.data == "admin_orders")
async def orders_menu_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📋 <b>Управление заказами</b>\n\n"
        "Выберите статус заказов для просмотра:",
        reply_markup=admin_kb.orders_menu
    )

@dp.callback_query(F.data.startswith("orders_"))
async def orders_list_handler(callback: types.CallbackQuery):
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

    session = Session()
    try:
        orders = session.query(Order).filter_by(status=status_map.get(status, "pending")).all()

        if not orders:
            await callback.message.edit_text(
                f"{status_text[status]}\n\n"
                "Заказов с таким статусом нет.",
                reply_markup=admin_kb.orders_menu
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
            reply_markup=admin_kb.orders_menu
        )
    finally:
        session.close()

# === УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ===

@dp.callback_query(F.data == "admin_users")
async def users_menu_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_kb.users_menu
    )

@dp.callback_query(F.data == "users_all")
async def users_all_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    session = Session()
    try:
        users = session.query(TelegramUser).limit(10).all()

        if not users:
            await callback.message.edit_text(
                "👥 Пользователей пока нет.",
                reply_markup=admin_kb.users_menu
            )
            return

        text = "👥 <b>Список пользователей:</b>\n\n"

        for user in users:
            status = "🚫" if user.is_banned else "✅"
            admin = "👮" if user.is_admin else ""
            text += f"{status} {admin} {user.first_name or 'Без имени'}\n"
            text += f"   @{user.username or 'нет username'}\n"
            text += f"   ID: {user.user_id}\n"
            text += f"   /user_{user.user_id}\n\n"

        await callback.message.edit_text(
            text,
            reply_markup=admin_kb.users_menu
        )
    finally:
        session.close()

# === СТАТИСТИКА ===

@dp.callback_query(F.data == "admin_stats")
async def stats_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    session = Session()
    try:
        # Подсчет статистики
        total_users = session.query(func.count(TelegramUser.id)).scalar()
        total_products = session.query(func.count(Product.id)).scalar()
        total_orders = session.query(func.count(Order.id)).scalar()

        # Подсчет заказов по статусам
        pending_orders = session.query(func.count(Order.id)).filter_by(status='pending').scalar()
        completed_orders = session.query(func.count(Order.id)).filter_by(status='completed').scalar()

        # Общая сумма продаж
        total_sales = session.query(func.sum(Order.total_price)).filter_by(status='completed').scalar() or 0

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
            reply_markup=admin_kb.admin_main_menu
        )
    finally:
        session.close()

# Обработка отмены действия
@dp.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Действие отменено",
        reply_markup=admin_kb.admin_main_menu
    )

# Закрытие админ-панели
@dp.callback_query(F.data == "admin_close")
async def close_admin_handler(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Панель закрыта")

# Обработка команд для просмотра конкретных элементов
@dp.message(F.text.regexp(r'^/product_(\d+)$'))
async def product_detail_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    product_id = int(message.text.split('_')[1])

    session = Session()
    try:
        product = session.query(Product).filter_by(id=product_id).first()

        if not product:
            await message.answer("❌ Товар не найден")
            return

        status = "✅ В наличии" if product.available else "❌ Нет в наличии"

        text = (
            f"📦 <b>{product.name}</b>\n\n"
            f"📝 {product.description}\n"
            f"💰 Цена: {product.price} руб.\n"
            f"📂 Категория: {product.category or 'Без категории'}\n"
            f"📊 Статус: {status}"
        )

        if product.image:
            await message.answer_photo(
                photo=product.image,
                caption=text,
                reply_markup=admin_kb.create_product_keyboard(product_id)
            )
        else:
            await message.answer(
                text,
                reply_markup=admin_kb.create_product_keyboard(product_id)
            )
    finally:
        session.close()

@dp.message(F.text.regexp(r'^/order_(\d+)$'))
async def order_detail_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    order_id = int(message.text.split('_')[1])

    session = Session()
    try:
        order = session.query(Order).filter_by(id=order_id).first()

        if not order:
            await message.answer("❌ Заказ не найден")
            return

        # Получаем позиции заказа
        items = session.query(OrderItem).filter_by(order_id=order_id).all()

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
            product = session.query(Product).filter_by(id=item.product_id).first()
            if product:
                text += f"• {product.name} x{item.quantity} = {item.price * item.quantity} руб.\n"

        text += f"\n💰 <b>Итого: {order.total_price} руб.</b>"

        await message.answer(
            text,
            reply_markup=admin_kb.create_order_keyboard(order_id)
        )
    finally:
        session.close()

@dp.message(F.text.regexp(r'^/user_(\d+)$'))
async def user_detail_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    user_id = int(message.text.split('_')[1])

    session = Session()
    try:
        user = session.query(TelegramUser).filter_by(user_id=user_id).first()

        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        # Подсчет заказов пользователя
        orders_count = session.query(func.count(Order.id)).filter_by(user_id=user_id).scalar()

        status = "🚫 Заблокирован" if user.is_banned else "✅ Активен"
        admin = "👮 Администратор" if user.is_admin else "👤 Пользователь"

        text = (
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"🆔 ID: {user.user_id}\n"
            f"📝 Имя: {user.first_name} {user.last_name or ''}\n"
            f"💬 Username: @{user.username or 'нет'}\n"
            f"📱 Телефон: {user.phone or 'Не указан'}\n"
            f"📊 Статус: {status}\n"
            f"🔐 Роль: {admin}\n"
            f"📋 Заказов: {orders_count}\n"
            f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}"
        )

        await message.answer(
            text,
            reply_markup=admin_kb.create_user_keyboard(user_id)
        )
    finally:
        session.close()

@dp.message(F.text)
async def cleaner(message: types.Message):
    # Удаляем пунктуацию и разбиваем на слова
    words = re.findall(r'\b\w+\b', message.text.lower())
    if restricted_words.intersection(words):
        await message.delete()
        await message.answer(f"{message.from_user.first_name}, вы не можете использовать эти слова!")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=[types.BotCommand(command='start', description='Начало работы'), types.BotCommand(command='menu', description='Меню')], scope=types.BotCommandScopeDefault())
    await dp.start_polling(bot)
asyncio.run(main())

