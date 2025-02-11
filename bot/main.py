import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import logging
from telegram.ext import Application, CommandHandler
from handlers import register_handlers
from config import BOT_TOKEN


def main():
    """
    Основная функция для запуска бота.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Запуск бота...")

    # Создаем объект Application (замена Updater в новых версиях)
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    register_handlers(application)

    # Запуск бота
    logging.info("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
