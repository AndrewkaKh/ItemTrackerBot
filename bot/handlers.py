from cgitb import reset

from telegram.ext import CommandHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from commands.admin_commands import load_products, reset_table_confirm, reset_table, cancel_reset, load_history
from commands.admin_commands import add_user, pay_user, reset_db, load_semifinished, handle_excel_file
from commands.report_commands import export_reports, filter_data, help_, start, watch_stock, unknown_command
from commands.user_commands import add_item, movement_from, movement_to, add_product, del_article, production




def register_handlers(application):
    """
    Регистрация всех обработчиков бота.
    """
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_product", add_product))
    application.add_handler(CommandHandler("add_item", add_item))
    application.add_handler(CommandHandler("ot", movement_from))
    application.add_handler(CommandHandler("po", movement_to))
    application.add_handler(CommandHandler("help", help_))
    application.add_handler(CommandHandler("del_article", del_article))
    application.add_handler(CommandHandler("pr", production))
    application.add_handler(CommandHandler("watch_stock", watch_stock))

    application.add_handler(CommandHandler("add_user", add_user))
    application.add_handler(CommandHandler("pay_user", pay_user))
    application.add_handler(CommandHandler("reset_db", reset_db))
    application.add_handler(CommandHandler("load_semifinished", load_semifinished))
    application.add_handler(CommandHandler("load_products", load_products))
    application.add_handler(CommandHandler("load_history", load_history))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_excel_file))
    application.add_handler(CallbackQueryHandler(reset_table_confirm, pattern="^reset_table:"))
    application.add_handler(CallbackQueryHandler(reset_table, pattern="^confirm_reset:"))
    application.add_handler(CallbackQueryHandler(cancel_reset, pattern="^cancel_reset$"))

    application.add_handler(CommandHandler("export_reports", export_reports))
    application.add_handler(CommandHandler("filter", filter_data))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
