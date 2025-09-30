"""
Обработчики админ-панели для управления продуктами
"""
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from src.config import ADMIN_IDS
from src.keyboards.admin import admin_kb
from src.services import ProductService
from src.bot.dependencies import get_db_session

router = Router()


class ProductStates(StatesGroup):
    """Состояния для работы с продуктами"""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_image = State()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


@router.callback_query(F.data == "admin_products")
async def products_menu_handler(callback: types.CallbackQuery):
    """Меню управления товарами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📦 <b>Управление товарами</b>\n\n"
        "Выберите действие:",
        reply_markup=admin_kb.products_menu()
    )


@router.callback_query(F.data == "product_list")
async def product_list_handler(callback: types.CallbackQuery):
    """Список всех товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    session = get_db_session()
    try:
        product_service = ProductService(session)
        products = product_service.get_all_products()

        if not products:
            await callback.message.edit_text(
                "📦 Товаров пока нет.\n"
                "Добавьте первый товар!",
                reply_markup=admin_kb.products_menu()
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
            reply_markup=admin_kb.products_menu()
        )
    finally:
        session.close()


@router.callback_query(F.data == "product_add")
async def product_add_handler(callback: types.CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await state.set_state(ProductStates.waiting_for_name)
    await callback.message.edit_text(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Шаг 1/5: Введите название товара:",
        reply_markup=admin_kb.cancel()
    )


@router.message(ProductStates.waiting_for_name)
async def product_name_handler(message: types.Message, state: FSMContext):
    """Обработка названия товара"""
    await state.update_data(name=message.text)
    await state.set_state(ProductStates.waiting_for_description)

    await message.answer(
        "Шаг 2/5: Введите описание товара:",
        reply_markup=admin_kb.cancel()
    )


@router.message(ProductStates.waiting_for_description)
async def product_description_handler(message: types.Message, state: FSMContext):
    """Обработка описания товара"""
    await state.update_data(description=message.text)
    await state.set_state(ProductStates.waiting_for_price)

    await message.answer(
        "Шаг 3/5: Введите цену товара (только число):",
        reply_markup=admin_kb.cancel()
    )


@router.message(ProductStates.waiting_for_price)
async def product_price_handler(message: types.Message, state: FSMContext):
    """Обработка цены товара"""
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(ProductStates.waiting_for_category)

        await message.answer(
            "Шаг 4/5: Введите категорию товара:",
            reply_markup=admin_kb.cancel()
        )
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число!")


@router.message(ProductStates.waiting_for_category)
async def product_category_handler(message: types.Message, state: FSMContext):
    """Обработка категории товара"""
    await state.update_data(category=message.text)
    await state.set_state(ProductStates.waiting_for_image)

    await message.answer(
        "Шаг 5/5: Отправьте фото товара или введите 'пропустить':",
        reply_markup=admin_kb.cancel()
    )


@router.message(ProductStates.waiting_for_image)
async def product_image_handler(message: types.Message, state: FSMContext):
    """Обработка изображения товара"""
    data = await state.get_data()

    image_path = None
    if message.photo:
        image_path = message.photo[-1].file_id
    elif message.text and message.text.lower() != 'пропустить':
        await message.answer("❌ Отправьте фото или введите 'пропустить'")
        return

    # Сохраняем товар в БД
    session = get_db_session()
    try:
        product_service = ProductService(session)
        product_data = {
            'name': data['name'],
            'description': data['description'],
            'price': data['price'],
            'category': data['category'],
            'image': image_path,
            'available': True
        }

        product = product_service.create_product(product_data)

        await message.answer(
            f"✅ Товар '<b>{product.name}</b>' успешно добавлен!\n\n"
            f"💰 Цена: {product.price} руб.\n"
            f"📂 Категория: {product.category}",
            reply_markup=admin_kb.products_menu()
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении товара: {str(e)}")
    finally:
        session.close()
        await state.clear()


@router.message(F.text.regexp(r'^/product_(\d+)$'))
async def product_detail_handler(message: types.Message):
    """Детали конкретного товара"""
    if not is_admin(message.from_user.id):
        return

    product_id = int(message.text.split('_')[1])

    session = get_db_session()
    try:
        product_service = ProductService(session)
        product = product_service.get_product_by_id(product_id)

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
                reply_markup=admin_kb.product_actions(product_id)
            )
        else:
            await message.answer(
                text,
                reply_markup=admin_kb.product_actions(product_id)
            )
    finally:
        session.close()