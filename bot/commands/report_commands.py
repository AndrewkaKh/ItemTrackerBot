from datetime import datetime
import os
import sys

from sqlalchemy.sql import text
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
import pandas as pd

from bot.access_control.auth_decorator import require_auth
from bot.config import ADMIN_ID, REPORT_FOLDER
from database.db import SessionLocal
from database.models import Movement
from reports.excel_generator import generate_excel, generate_excel_for_movement



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))



def fetch_as_dicts(result):
    """ Преобразование результата запроса в список словарей """
    keys = result.keys()
    return [dict(zip(keys, row)) for row in result.fetchall()]

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

        greeting = f"Привет, {update.effective_user.first_name}! 👋\n"
        greeting += "Добро пожаловать в систему управления складом.\n"

        common_commands = """
📊 Команды отчетов (доступны всем пользователям):
- /export_reports - Сгенерировать отчет об остатках и движении товаров (Excel).
- /filter <Дата начала> <Дата конца> - Отфильтровать данные за указанный период.
        """

        user_commands = """
💼 Команды для пользователей:
- /add_item <Артикул>; <Название>; <Стоимость>; <Ответственный> - Добавить полуфабрикат.
- /movement <Артикул>; <Поступление>; <Отгрузка>[; Комментарий] - Добавить движение товаров.
- /add_product <Название>; <Артикул>; <Состав> - Добавить товар и его состав.
- /del_article <Артикул> - Удалить полуфабрикат или товар.
        """

        admin_commands = """
🔧 Дополнительные команды для администратора:
- /add_user <username>; <Имя>; <Фамилия> - Добавить нового пользователя.
- /pay_user <username> <сумма> - Выплатить пользователю.
- /reset_db - Сбросить определенную таблицу или сбросить всё.
- /load_semifinished - Загрузить полуфабрикаты из файла.
- /load_products - Загрузить товары и их состав из файла.
- /load_history - Загрузить историю склада из файла.
        """

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
    Экспорт всех отчетов (остатки, движение товаров, полуфабрикаты и товары) в Excel.
    """
    try:
        db = SessionLocal()

        stock_query = text("""
            SELECT 
                article AS Артикул, 
                name AS Наименование, 
                in_stock AS Остаток, 
                cost AS Стоимость
            FROM stock
        """)
        stock_data = fetch_as_dicts(db.execute(stock_query))

        movement_query = text("""
            SELECT 
                date AS Дата, 
                name AS Наименование, 
                incoming AS Поступление, 
                outgoing AS Отгрузка, 
                comment AS Комментарий
            FROM movements
        """)
        movement_data = fetch_as_dicts(db.execute(movement_query))

        stock_pay_user_query = text("""
            SELECT
                username AS Пользователь,
                role AS Роль,
                expenses AS "Остаток средств"
            FROM users
        """)
        stock_pay_user_data = fetch_as_dicts(db.execute(stock_pay_user_query))

        semi_finished_products_query = text("""
            SELECT
                article AS Артикул,
                name AS Наименование,
                cost AS Стоимость,
                responsible AS Ответственный,
                comment AS Комментарий
            FROM semi_finished_products
        """)
        semi_finished_products = fetch_as_dicts(db.execute(semi_finished_products_query))

        products_query = text("""
            SELECT 
                pc.product_article AS Артикул,
                pc.product_name AS Наименование,
                STRING_AGG(pcomp.semi_product_article || ' (' || pcomp.quantity || ')', ', ') AS Состав
            FROM product_composition pc
            LEFT JOIN product_component pcomp ON pc.product_article = pcomp.product_article
            GROUP BY pc.product_article, pc.product_name
        """)
        products = fetch_as_dicts(db.execute(products_query))

        report_file = generate_excel(stock_data, movement_data, stock_pay_user_data, semi_finished_products, products)

        with open(report_file, "rb") as f:
            await update.message.reply_document(f)

        db.close()
        await update.message.reply_text("Отчеты успешно сгенерированы и отправлены!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при экспорте отчетов: {str(e)}")


@require_auth
async def filter_data(update: Update, context: CallbackContext):
    """
    Фильтрация данных по периоду и генерация отчета в формате Excel.
    Пример команды: /filter 2023-01-01 2023-12-31
    """
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Неверное количество аргументов. Пример: /filter 2023-01-01 2023-12-31")
            return

        start_date = datetime.strptime(args[0], "%Y-%m-%d")
        end_date = datetime.strptime(args[1], "%Y-%m-%d")

        db = SessionLocal()

        query = db.query(Movement).filter(Movement.date.between(start_date, end_date))
        movements = query.all()

        if not movements:
            await update.message.reply_text("Данных за указанный период не найдено.")
            return

        data = [{
            "Дата": movement.date.strftime("%Y-%m-%d %H:%M:%S"),
            "Артикул": movement.article,
            "Название": movement.name,
            "Поступление": movement.incoming,
            "Отгрузка": movement.outgoing,
            "Комментарий": movement.comment
        } for movement in movements]

        df = pd.DataFrame(data)
        file = generate_excel_for_movement(df)
        with open(file, "rb") as f:
            await update.message.reply_document(f)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")