"""
Обработчики для работы с каталогом и корзиной
"""
import os
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, FSInputFile

from src.services import ProductService, CartService, OrderService
from src.config import PAYMENT_TOKEN
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
    import logging
    logger = logging.getLogger(__name__)

    parts = callback.data.split(":")
    product_id = int(parts[1])

    data = await state.get_data()
    quantity = data.get("quantity", 1)

    logger.info(f"Добавление товара в корзину: user_id={callback.from_user.id}, product_id={product_id}, quantity={quantity}")

    session = get_db_session()
    try:
        cart_service = CartService(session)
        cart_item = cart_service.add_to_cart(
            user_id=callback.from_user.id,
            product_id=product_id,
            quantity=quantity
        )
        logger.info(f"Товар добавлен в корзину: cart_item_id={cart_item.id}")

        # Сбрасываем количество
        await state.update_data(quantity=1)

        await callback.answer(
            f"✅ Добавлено в корзину ({quantity} шт.)",
            show_alert=True
        )

    except Exception as e:
        logger.error(f"Ошибка при добавлении в корзину: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при добавлении в корзину", show_alert=True)
    finally:
        session.close()


@router.callback_query(F.data == "show_cart")
async def show_cart(callback: types.CallbackQuery):
    """Показать корзину"""
    import logging
    logger = logging.getLogger(__name__)

    session = get_db_session()
    try:
        cart_service = CartService(session)
        cart_items = cart_service.get_user_cart(callback.from_user.id)
        logger.info(f"Корзина пользователя {callback.from_user.id}: {len(cart_items)} товаров")

        if not cart_items:
            cart_text = (
                "🛒 <b>КОРЗИНА</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                "📭 Ваша корзина пуста\n\n"
                "Загляните в наше меню и выберите\n"
                "что-то вкусное! 🍕"
            )
            keyboard = get_main_menu_keyboard()
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

        # Если сообщение содержит фото, удаляем и отправляем новое
        try:
            await callback.message.edit_text(cart_text, reply_markup=keyboard)
        except Exception:
            # Если не получилось отредактировать (например, это было фото), удаляем и отправляем новое
            await callback.message.delete()
            await callback.message.answer(cart_text, reply_markup=keyboard)

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при показе корзины: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке корзины", show_alert=True)
    finally:
        session.close()


@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    """Очистить корзину"""
    session = get_db_session()
    try:
        cart_service = CartService(session)
        cart_service.clear_cart(callback.from_user.id)

        text = (
            "🗑 <b>КОРЗИНА ОЧИЩЕНА</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Все товары удалены из корзины\n\n"
            "Хотите начать новый заказ?\n"
            "Загляните в наше меню! 🍕"
        )

        try:
            await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
        except Exception:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=get_main_menu_keyboard())

        await callback.answer("✅ Корзина очищена", show_alert=True)

    finally:
        session.close()


@router.callback_query((F.data == "back_to_catalog") | (F.data == "show_catalog"))
async def back_to_catalog(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к каталогу"""
    session = get_db_session()
    try:
        product_service = ProductService(session)
        products = product_service.get_all_products(available_only=True)

        if not products:
            text = "🍕 <b>Каталог временно недоступен</b>\n\n" \
                   "Попробуйте позже!"
            try:
                await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
            except Exception:
                await callback.message.delete()
                await callback.message.answer(text, reply_markup=get_main_menu_keyboard())
        else:
            # Сохраняем список товаров в состояние
            await state.update_data(products=products, current_index=0, quantity=1)

            # Показываем первый товар
            product = products[0]
            # Удаляем текстовое сообщение и отправляем фото
            await callback.message.delete()
            await show_product_send(
                callback.message, product, 0, products, callback.from_user.id
            )

        await callback.answer()

    finally:
        session.close()


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    """Показать главное меню"""
    text = "📋 <b>ГЛАВНОЕ МЕНЮ</b>\n\n" \
           "Выберите раздел:"

    try:
        await callback.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=get_main_menu_keyboard())

    await callback.answer()


@router.callback_query(F.data == "show_contacts")
async def show_contacts(callback: types.CallbackQuery):
    """Показать контакты"""
    contacts_text = (
        "📞 <b>КОНТАКТЫ И ИНФОРМАЦИЯ</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "🍕 <b>Пиццерия Pizza Bot</b>\n\n"
        "📍 <b>Адрес:</b>\n"
        "г. Москва, ул. Примерная, д. 1\n"
        "(рядом с метро «Примерная»)\n\n"
        "📞 <b>Телефон для заказов:</b>\n"
        "+7 (999) 123-45-67\n\n"
        "⏰ <b>Время работы:</b>\n"
        "Ежедневно: 10:00 - 22:00\n"
        "Без выходных\n\n"
        "🚚 <b>Доставка:</b>\n"
        "• Бесплатно от 1000 руб.\n"
        "• Среднее время: 30-45 минут\n"
        "• По всей Москве\n\n"
        "💳 <b>Оплата:</b>\n"
        "Наличными, картой, онлайн\n\n"
        "💬 Будем рады вашему заказу!"
    )

    try:
        await callback.message.edit_text(contacts_text, reply_markup=get_main_menu_keyboard())
    except Exception:
        await callback.message.delete()
        await callback.message.answer(contacts_text, reply_markup=get_main_menu_keyboard())

    await callback.answer()


@router.callback_query(F.data == "checkout")
async def checkout(callback: types.CallbackQuery, state: FSMContext):
    """Оформление заказа с оплатой"""
    session = get_db_session()
    try:
        cart_service = CartService(session)
        cart_items = cart_service.get_user_cart(callback.from_user.id)

        if not cart_items:
            await callback.answer("❌ Корзина пуста!", show_alert=True)
            return

        # Сохраняем корзину в состояние для последующей обработки
        await state.update_data(cart_items=cart_items)

        # Проверяем, настроена ли оплата
        if not PAYMENT_TOKEN:
            # Если токен не настроен, создаем заказ без оплаты
            await create_order_without_payment(callback, cart_items, session)
        else:
            # Отправляем инвойс для оплаты
            await send_invoice(callback, cart_items)

        await callback.answer()

    finally:
        session.close()


async def create_order_without_payment(callback, cart_items, session):
    """Создание заказа без оплаты"""
    order_service = OrderService(session)

    order_data = {
        'user_id': callback.from_user.id,
        'status': 'pending',
        'phone': None,
        'address': None
    }

    items = [
        {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'price': item['product_price']
        }
        for item in cart_items
    ]

    order = order_service.create_order(order_data, items)

    # Очищаем корзину после создания заказа
    cart_service = CartService(session)
    cart_service.clear_cart(callback.from_user.id)

    # Формируем сообщение о заказе
    total_price = sum(item['total'] for item in cart_items)
    order_text = f"✅ <b>ЗАКАЗ ОФОРМЛЕН!</b>\n"
    order_text += "━━━━━━━━━━━━━━━━━━━\n\n"
    order_text += f"📦 <b>Номер заказа: #{order.id}</b>\n\n"
    order_text += "<b>Состав заказа:</b>\n"

    for item in cart_items:
        order_text += f"• {item['product_name']}\n"
        order_text += f"  {item['quantity']} шт. × {item['product_price']:.0f} = "
        order_text += f"<b>{item['total']:.0f} руб.</b>\n\n"

    order_text += "━━━━━━━━━━━━━━━━━━━\n"
    order_text += f"💰 <b>ИТОГО: {total_price:.0f} руб.</b>\n\n"
    order_text += "📞 Наш менеджер свяжется с вами\n"
    order_text += "для подтверждения заказа в течение 10 минут\n\n"
    order_text += "⏰ <b>Статус:</b> Ожидает подтверждения\n"
    order_text += "🚚 <b>Доставка:</b> 30-45 минут после подтверждения"

    try:
        await callback.message.edit_text(order_text, reply_markup=get_main_menu_keyboard())
    except Exception:
        await callback.message.delete()
        await callback.message.answer(order_text, reply_markup=get_main_menu_keyboard())


async def send_invoice(callback, cart_items):
    """Отправка инвойса для оплаты"""
    from aiogram.types import LabeledPrice

    # Формируем описание заказа
    description = "Заказ в Pizza Bot:\n"
    for item in cart_items:
        description += f"• {item['product_name']} x{item['quantity']}\n"

    # Формируем позиции для оплаты
    prices = []
    for item in cart_items:
        prices.append(
            LabeledPrice(
                label=f"{item['product_name']} x{item['quantity']}",
                amount=int(item['total'] * 100)  # Сумма в копейках
            )
        )

    total_amount = int(sum(item['total'] for item in cart_items) * 100)

    # Отправляем инвойс
    await callback.message.answer_invoice(
        title="Оплата заказа Pizza Bot",
        description=description,
        payload=f"order_{callback.from_user.id}",
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="pizza-bot-payment",
        photo_url="https://via.placeholder.com/400x300.png?text=Pizza+Bot",
        photo_width=400,
        photo_height=300,
        need_name=True,
        need_phone_number=True,
        need_email=False,
        need_shipping_address=True,
        is_flexible=False
    )


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Обработка предоплатной проверки"""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: types.Message, state: FSMContext):
    """Обработка успешной оплаты"""
    import logging
    logger = logging.getLogger(__name__)

    payment_info = message.successful_payment
    logger.info(f"Успешная оплата: user_id={message.from_user.id}, "
                f"amount={payment_info.total_amount/100} {payment_info.currency}")

    session = get_db_session()
    try:
        # Получаем корзину из состояния
        data = await state.get_data()
        cart_items = data.get('cart_items', [])

        if not cart_items:
            await message.answer(
                "❌ Ошибка: корзина пуста",
                reply_markup=get_main_menu_keyboard()
            )
            return

        # Создаем заказ
        order_service = OrderService(session)

        order_data = {
            'user_id': message.from_user.id,
            'status': 'paid',
            'phone': payment_info.order_info.phone_number if payment_info.order_info else None,
            'address': None
        }

        items = [
            {
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'price': item['product_price']
            }
            for item in cart_items
        ]

        order = order_service.create_order(order_data, items)

        # Очищаем корзину
        cart_service = CartService(session)
        cart_service.clear_cart(message.from_user.id)

        # Очищаем состояние
        await state.clear()

        # Формируем сообщение
        total_price = sum(item['total'] for item in cart_items)
        order_text = f"✅ <b>ОПЛАТА УСПЕШНА!</b>\n"
        order_text += "━━━━━━━━━━━━━━━━━━━\n\n"
        order_text += f"🎉 Спасибо за покупку!\n\n"
        order_text += f"📦 <b>Номер заказа: #{order.id}</b>\n"
        order_text += f"💳 <b>Оплачено: {total_price:.0f} руб.</b>\n\n"
        order_text += "<b>Состав заказа:</b>\n"

        for item in cart_items:
            order_text += f"• {item['product_name']}\n"
            order_text += f"  {item['quantity']} шт. × {item['product_price']:.0f} = "
            order_text += f"<b>{item['total']:.0f} руб.</b>\n\n"

        order_text += "━━━━━━━━━━━━━━━━━━━\n\n"
        order_text += "🚚 <b>Ваш заказ принят в работу!</b>\n\n"
        order_text += "📞 Мы свяжемся с вами для уточнения\n"
        order_text += "деталей доставки в течение 10 минут\n\n"
        order_text += "⏰ Ожидаемое время доставки: 30-45 минут\n\n"
        order_text += "Приятного аппетита! 🍕"

        await message.answer(order_text, reply_markup=get_main_menu_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при обработке оплаты: {e}", exc_info=True)
        await message.answer(
            "❌ Произошла ошибка при обработке заказа. Свяжитесь с поддержкой.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        session.close()


async def show_product_send(message, product, index, products, user_id):
    """Вспомогательная функция для отправки нового сообщения с товаром"""
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
                await message.answer_photo(
                    photo=product.image,
                    caption=caption,
                    reply_markup=keyboard
                )
            # Если это локальный файл
            elif os.path.exists(product.image):
                photo = FSInputFile(product.image)
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=keyboard
                )
            else:
                raise FileNotFoundError("Image not found")
        except Exception:
            text = f"🖼 <i>Фото временно недоступно</i>\n\n{caption}"
            await message.answer(text, reply_markup=keyboard)
    else:
        text = f"🖼 <i>Фото отсутствует</i>\n\n{caption}"
        await message.answer(text, reply_markup=keyboard)


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
    if product.image:
        try:
            # Если это file_id от Telegram, используем его напрямую
            if product.image.startswith('AgAC') or product.image.startswith('BAA'):
                media = InputMediaPhoto(media=product.image, caption=caption, parse_mode="HTML")
            # Если это локальный файл
            elif os.path.exists(product.image):
                photo = FSInputFile(product.image)
                media = InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML")
            else:
                raise FileNotFoundError("Image not found")

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