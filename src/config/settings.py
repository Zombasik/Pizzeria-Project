"""
Конфигурация приложения
"""
import os
from typing import List

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8420167575:AAHBJCqJ1Urg7ftCwpmvfwsSAmL3ka4RePA')

# ID администраторов бота
# Замените на реальные Telegram ID администраторов
ADMIN_IDS: List[int] = [
    1984883401,  # Главный администратор (может добавлять других админов)
    # Добавьте других администраторов здесь
]

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/pizza_bot.db')

# Секретный ключ для Flask (ОБЯЗАТЕЛЬНО измените в продакшене!)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# URL админки (для веб-версии, если потребуется)
ADMIN_URL = os.getenv('ADMIN_URL', 'http://localhost:5000')

# Время жизни токена авторизации (в часах)
TOKEN_LIFETIME_HOURS = int(os.getenv('TOKEN_LIFETIME_HOURS', '1'))

# Запрещенные слова для фильтра
RESTRICTED_WORDS = {'нахуй', 'жопу', 'нафиг'}

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/pizza_bot.log')

# Настройки пагинации
ITEMS_PER_PAGE = 10

# Максимальный размер файла для загрузки (в байтах)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Токен платежной системы (Юkassa, Stripe и т.д.)
# Для тестирования используйте тестовый токен
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN', '')