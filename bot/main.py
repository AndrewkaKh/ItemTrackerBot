import logging
import os
import sys

from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN
from handlers import register_handlers

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def main():
    """
    Основная функция для запуска бота.
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Запуск бота...")

    application = Application.builder().token(BOT_TOKEN).build()

    register_handlers(application)

    logging.info("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
