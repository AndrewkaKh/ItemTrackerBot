from telegram.ext import CommandHandler, CallbackContext
from telegram import Update
import os
from sqlalchemy.sql import text

from bot.access_control.auth_decorator import require_auth
from bot.config import ADMIN_ID, REPORT_FOLDER
from database.db import SessionLocal
from reports.excel_generator import generate_excel
from reports.pdf_generator import generate_pdf

@require_auth
async def start(update: Update, context: CallbackContext):
    """
    Приветственная команда /start.
    Показывает доступные команды в зависимости от роли пользователя (админ или пользователь).
    """
    db = SessionLocal()
    try:
        user_id = update.effective_user.id  # ID текущего пользователя
        is_admin = str(user_id) == ADMIN_ID  # Сравниваем с ID администратора из конфигурации

        # Приветственное сообщение
        greeting = f"Привет, {update.effective_user.first_name}! 👋\n"
        greeting += "Добро пожаловать в систему управления складом.\n"

        # Команды, доступные всем пользователям
        common_commands = """
📊 Команды отчетов (доступны всем пользователям):
- /export_reports - Сгенерировать отчет об остатках и движении товаров (Excel и PDF).
- /filter <Дата начала> <Дата конца> - Отфильтровать данные за указанный период.
        """

        # Команды для пользователей
        user_commands = """
💼 Команды для пользователей:
- /add_item <Артикул>; <Название>; <Стоимость>; <Ответственный> - Добавить полуфабрикат.
- /movement <Артикул>; <Поступление>; <Отгрузка>[; Комментарий] - Добавить движение товаров.
- /add_product <Название>; <Артикул>; <Состав> - Добавить товар и его состав.
- /delete <Артикул> - Удалить полуфабрикат или товар.
        """

        # Команды для администратора
        admin_commands = """
🔧 Дополнительные команды для администратора:
- /add_user <username>; <Имя>; <Фамилия> - Добавить нового пользователя.
- /pay_user <username> <сумма> - Выплатить пользователю.
- /reset_db - Сбросить базу данных (пересоздать таблицы).
        """

        # Формирование сообщения для администратора и пользователя
        if is_admin:
            greeting += common_commands + user_commands + admin_commands
        else:
            greeting += common_commands + user_commands

        await update.message.reply_text(greeting)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при выполнении команды /start: {str(e)}")

@require_auth
async def export_reports(update: Update, context: CallbackContext):
    """
    Экспорт всех отчетов (остатки и движение товаров) в Excel и PDF.
    """
    try:
        # Подключение к базе данных
        db = SessionLocal()

        # Получение данных для отчетов
        stock_query = text("""
            SELECT 
                article AS Артикул, 
                name AS Наименование, 
                in_stock AS Остаток, 
                cost AS Стоимость
            FROM stock
        """)
        stock_data = db.execute(stock_query).fetchall()

        movement_query = text("""
            SELECT 
                date AS Дата, 
                name AS Наименование, 
                incoming AS Поступление, 
                outgoing AS Отгрузка, 
                comment AS Комментарий
            FROM movements
        """)
        movement_data = db.execute(movement_query).fetchall()

        stock_pay_user_query = text("""
            SELECT
                first_name AS Имя,
                second_name AS Фамилия,
                expenses AS "Остаток средств"
            FROM users
        """)
        stock_pay_user_data = db.execute(stock_pay_user_query).fetchall()

        # Генерация отчетов
        generate_excel(stock_data, movement_data, stock_pay_user_data)
        report_file = os.path.join(REPORT_FOLDER, "warehouse_report.xlsx")

        # Отправка отчетов пользователю
        with open(report_file, "rb") as f:
            await update.message.reply_document(f)

        await update.message.reply_text("Отчеты успешно сгенерированы и отправлены!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при экспорте отчетов: {str(e)}")
    finally:
        db.close()

@require_auth
async def filter_data(update: Update, context: CallbackContext):
    """
    Фильтрация данных по периоду и генерация отчетов.
    Пример команды: /filter 2023-01-01 2023-12-31
    """
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Пример: /filter 2023-01-01 2023-12-31")
            return

        start_date, end_date = args[0], args[1]

        # Подключение к базе данных
        db = SessionLocal()

        # Применение фильтров
        movement_query = text("""
            SELECT date AS Дата, name AS Наименование, incoming AS Поступление, 
                   outgoing AS Отгрузка, comment AS Комментарий
            FROM movements
            WHERE date BETWEEN :start_date AND :end_date
        """)
        filtered_movements = db.execute(movement_query, {"start_date": start_date, "end_date": end_date}).fetchall()

        # Преобразуем отфильтрованные данные для отчетов
        stock_data = []  # Здесь можно настроить остатки по полуфабрикатам
        movement_data = [
            {
                "Дата": m.date,
                "Наименование": m.name,
                "Поступление": m.incoming,
                "Отгрузка": m.outgoing,
                "Комментарий": m.comment,
            }
            for m in filtered_movements
        ]

        # Генерация отчетов
        excel_files = generate_excel(stock_data, movement_data)
        pdf_files = generate_pdf(stock_data, movement_data)

        # Отправка отчетов пользователю
        for file in excel_files + pdf_files:
            with open(file, "rb") as f:
                await update.message.reply_document(f)

        await update.message.reply_text(f"Данные за период {start_date} - {end_date} успешно отфильтрованы и отправлены!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при фильтрации данных: {str(e)}")
    finally:
        db.close()

