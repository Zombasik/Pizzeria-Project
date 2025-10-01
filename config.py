# Конфигурация бота и админки

# Telegram Bot Token
BOT_TOKEN = '8420167575:AAHBJCqJ1Urg7ftCwpmvfwsSAmL3ka4RePA'

# ID администраторов бота
# Замените на реальные Telegram ID администраторов
# Чтобы узнать свой ID, отправьте боту любое сообщение и посмотрите в консоли
ADMIN_IDS = [
    1984883401,  # Главный администратор (может добавлять других админов)
    # 987654321,  # Добавьте других администраторов здесь
]

# Настройки базы данных
DATABASE_URL = 'sqlite:///pizza_bot.db'

# Секретный ключ для Flask (ОБЯЗАТЕЛЬНО измените в продакшене!)
SECRET_KEY = 'your-secret-key-change-this-in-production'

# URL админки
ADMIN_URL = 'http://localhost:5000'

# Время жизни токена авторизации (в часах)
TOKEN_LIFETIME_HOURS = 1

# Запрещенные слова для фильтра
RESTRICTED_WORDS = {'какашка', 'попа', 'нафиг'}