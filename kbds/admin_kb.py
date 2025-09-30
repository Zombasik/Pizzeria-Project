from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню админки
admin_main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Управление товарами", callback_data="admin_products")],
    [InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")],
    [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
    [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
    [InlineKeyboardButton(text="❌ Закрыть", callback_data="admin_close")]
])

# Меню управления товарами
products_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Добавить товар", callback_data="product_add")],
    [InlineKeyboardButton(text="📝 Список товаров", callback_data="product_list")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
])

# Меню управления заказами
orders_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🆕 Новые заказы", callback_data="orders_new")],
    [InlineKeyboardButton(text="🔄 В обработке", callback_data="orders_processing")],
    [InlineKeyboardButton(text="✅ Выполненные", callback_data="orders_completed")],
    [InlineKeyboardButton(text="❌ Отмененные", callback_data="orders_cancelled")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
])

# Меню управления пользователями
users_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="👥 Все пользователи", callback_data="users_all")],
    [InlineKeyboardButton(text="🚫 Заблокированные", callback_data="users_banned")],
    [InlineKeyboardButton(text="👮 Администраторы", callback_data="users_admins")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
])

def create_product_keyboard(product_id):
    """Создает клавиатуру для управления конкретным товаром"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"product_edit:{product_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"product_delete:{product_id}")
        ],
        [
            InlineKeyboardButton(text="📷 Изменить фото", callback_data=f"product_photo:{product_id}"),
            InlineKeyboardButton(text="🔄 Доступность", callback_data=f"product_toggle:{product_id}")
        ],
        [InlineKeyboardButton(text="🔙 К списку", callback_data="product_list")]
    ])

def create_order_keyboard(order_id):
    """Создает клавиатуру для управления заказом"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"order_accept:{order_id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"order_cancel:{order_id}")
        ],
        [
            InlineKeyboardButton(text="📦 В доставке", callback_data=f"order_delivering:{order_id}"),
            InlineKeyboardButton(text="✔️ Завершен", callback_data=f"order_complete:{order_id}")
        ],
        [InlineKeyboardButton(text="🔙 К заказам", callback_data="admin_orders")]
    ])

def create_user_keyboard(user_id):
    """Создает клавиатуру для управления пользователем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"user_ban:{user_id}"),
            InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"user_unban:{user_id}")
        ],
        [
            InlineKeyboardButton(text="👮 Сделать админом", callback_data=f"user_admin:{user_id}"),
            InlineKeyboardButton(text="📋 История заказов", callback_data=f"user_orders:{user_id}")
        ],
        [InlineKeyboardButton(text="🔙 К пользователям", callback_data="admin_users")]
    ])

# Клавиатура подтверждения
def confirm_keyboard(action):
    """Создает клавиатуру подтверждения действия"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
        ]
    ])

# Клавиатура для навигации по спискам
def pagination_keyboard(page, total_pages, prefix):
    """Создает клавиатуру для пагинации"""
    buttons = []

    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}_page:{page-1}"))

    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))

    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}_page:{page+1}"))

    return InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])

# Клавиатура отмены действия
cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
])