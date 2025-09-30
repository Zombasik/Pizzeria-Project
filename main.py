"""
Главный файл запуска бота
"""
import asyncio
import logging
import sys
import os

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bot import (
    setup_logging, create_bot, create_dispatcher,
    setup_bot_commands, get_db_manager
)


async def main():
    """Главная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Запуск Pizza Bot...")

    try:
        # Инициализация базы данных
        db_manager = get_db_manager()
        logger.info("База данных инициализирована")

        # Создание бота и диспетчера
        bot = create_bot()
        dp = create_dispatcher()

        # Настройка команд бота
        await setup_bot_commands(bot)
        logger.info("Команды бота настроены")

        # Очистка вебхуков
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Вебхуки очищены")

        # Запуск поллинга
        logger.info("Бот запущен и готов к работе!")
        print("Bot successfully started! Press Ctrl+C to stop.")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        logger.info("Бот завершает работу...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)