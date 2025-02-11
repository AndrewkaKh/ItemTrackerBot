from cgitb import reset

from telegram.ext import CommandHandler, CallbackQueryHandler

from commands.admin_commands import add_user, pay_user, reset_db, confirm_reset_db, cancel_reset_db
from commands.report_commands import export_reports, filter_data
from commands.user_commands import add_item, movement, add_product, del_article
from commands.report_commands import start

def register_handlers(application):
    """
    Регистрация всех обработчиков бота.
    """
    application.add_handler(CommandHandler("start", start))
    # Команды пользователей
    application.add_handler(CommandHandler("add_product", add_product))
    application.add_handler(CommandHandler("add_item", add_item))
    application.add_handler(CommandHandler("movement", movement))
    application.add_handler(CommandHandler("del_article", del_article))

    # Команды администратора
    application.add_handler(CommandHandler("add_user", add_user))
    application.add_handler(CommandHandler("pay_user", pay_user))
    application.add_handler(CommandHandler("reset_db", reset_db))
    application.add_handler(CallbackQueryHandler(confirm_reset_db, pattern="^confirm_reset_db$"))
    application.add_handler(CallbackQueryHandler(cancel_reset_db, pattern="^cancel_reset_db$"))

    # Генерация отчетов
    application.add_handler(CommandHandler("export_reports", export_reports))
    application.add_handler(CommandHandler("filter", filter_data))
