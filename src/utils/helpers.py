"""
Вспомогательные функции
"""
import re
from typing import List, Optional
from datetime import datetime


def format_price(price: float) -> str:
    """Форматирование цены"""
    return f"{price:.2f} руб."


def format_datetime(dt: datetime) -> str:
    """Форматирование даты и времени"""
    return dt.strftime("%d.%m.%Y %H:%M")


def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    phone_pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(phone_pattern, phone))


def clean_phone(phone: str) -> str:
    """Очистка номера телефона"""
    clean = re.sub(r'[^\d]', '', phone)
    if clean.startswith('8'):
        clean = '7' + clean[1:]
    elif clean.startswith('9'):
        clean = '7' + clean
    return clean


def paginate_list(items: List, page: int, per_page: int = 10) -> tuple:
    """Пагинация списка"""
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return items[start_idx:end_idx], total_pages


def escape_html(text: str) -> str:
    """Экранирование HTML символов"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста с многоточием"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def extract_user_id_from_command(text: str) -> Optional[int]:
    """Извлечение user_id из команды типа /user_123"""
    match = re.search(r'_(\d+)$', text)
    return int(match.group(1)) if match else None


def format_order_status(status: str) -> str:
    """Форматирование статуса заказа для отображения"""
    status_map = {
        'pending': '🆕 Новый',
        'processing': '🔄 В обработке',
        'preparing': '👨‍🍳 Готовится',
        'delivering': '🚗 Доставляется',
        'completed': '✅ Завершен',
        'cancelled': '❌ Отменен'
    }
    return status_map.get(status, status)