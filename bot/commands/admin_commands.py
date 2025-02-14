import sys
import os
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from telegram.ext import CommandHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from database.db import reset_database, SessionLocal
from sqlalchemy import text
import pandas as pd
from sqlalchemy.exc import IntegrityError

from bot.config import ADMIN_ID
from database.models import User, SemiFinishedProduct, ProductComposition, ProductComponent

# Список таблиц в базе данных
TABLES = {
    "users": "Пользователи",
    "movements": "Движение товаров",
    "all_db": "Все таблицы"
}

async def reset_db(update: Update, context: CallbackContext):
    """Предложить пользователю выбрать таблицу для очистки."""
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return

    keyboard = [[InlineKeyboardButton(name, callback_data=f"reset_table:{table}")]
                for table, name in TABLES.items()]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите таблицу, которую хотите очистить:", reply_markup=reply_markup)


async def reset_table_confirm(update: Update, context: CallbackContext):
    """Подтверждение очистки выбранной таблицы."""
    query = update.callback_query
    _, table_name = query.data.split(":")

    if str(query.from_user.id) != ADMIN_ID:
        await query.answer("У вас нет прав для выполнения этой команды.", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data=f"confirm_reset:{table_name}")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Вы выбрали таблицу '{TABLES[table_name]}'. Подтвердите удаление всех записей из этой таблицы.",
        reply_markup=reply_markup
    )


async def reset_table(update: Update, context: CallbackContext):
    query = update.callback_query
    _, table_name = query.data.split(":")

    db = SessionLocal()
    try:
        if table_name == "all_db":
            reset_database()
            await query.edit_message_text("✅ Все таблицы успешно очищены.")
        else:
            db.execute(text(f"DELETE FROM {table_name}"))
            db.commit()
            await query.edit_message_text(f"✅ Таблица '{TABLES[table_name]}' успешно очищена.")
    except Exception as e:
        await query.edit_message_text(f"Ошибка при очистке таблицы '{TABLES[table_name]}': {str(e)}")
    finally:
        db.close()


async def cancel_reset(update: Update, context: CallbackContext):
    """Обработка отмены действия."""
    query = update.callback_query
    await query.edit_message_text("❌ Действие отменено.")

async def add_user(update: Update, context: CallbackContext):
    """
    Команда для добавления нового пользователя.
    Пример: /add_user <username>;<Имя>;<Фамилия>
    """
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    try:
        args = " ".join(context.args)
        if ";" not in args:
            await update.message.reply_text(
                "Неверный формат аргументов.\nПример: /add_user Andrewka_Kh; Андрей; Храмов"
            )
            return

        parts = args.split(";")
        if len(parts) < 3:
            await update.message.reply_text(
                "Неверное количество аргументов.\nПример: /add_user Andrewka_Kh; Андрей; Храмов"
            )
            return

        username, first_name, second_name = parts[0].strip(), parts[1].strip(), parts[2].strip()

        # Проверяем существование пользователя в базе
        db = SessionLocal()
        existing_user = db.query(User).filter_by(username=username).first()
        if existing_user:
            await update.message.reply_text(f"Пользователь {username} уже существует.")
            db.close()
            return

        # Добавляем нового пользователя
        new_user = User(username=username, first_name=first_name, second_name=second_name)
        db.add(new_user)
        db.commit()
        db.close()

        await update.message.reply_text(f"Пользователь {username} успешно добавлен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def pay_user(update: Update, context: CallbackContext):
    """
    Команда для выплаты пользователю.
    Пример: /pay_user <username> <сумма>
    """
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Пример: /pay_user username сумма")
            return

        username = args[0].strip()
        amount = float(args[1])

        # Создаем сессию
        db = SessionLocal()

        # Проверяем существование пользователя
        user = db.query(User).filter_by(username=username).first()
        if not user:
            await update.message.reply_text(f"Пользователь {username} не найден.")
            db.close()
            return

        # Зачисляем деньги на счет пользователя
        user.expenses += amount
        db.commit()
        db.close()

        await update.message.reply_text(
            f"На счет пользователя {username} зачислено {amount} единиц. "
            f"Новый баланс: {user.expenses}."
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def load_semifinished(update: Update, context: CallbackContext):
    """Команда для загрузки данных о полуфабрикатах из Excel-файла."""
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    await update.message.reply_text("Пожалуйста, отправьте Excel-файл с данными о полуфабрикатах в формате:\n"
                                    "Артикул | Наименование | Стоимость | Ответственный")

async def load_products(update: Update, context: CallbackContext):
    """Команда для загрузки данных о полуфабрикатах из Excel-файла."""
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    await update.message.reply_text("Пожалуйста, отправьте Excel-файл с данными о товарах в формате:\n"
                                    "Название товара | Артикул товара | Состав | Ответственный | Комментарий")

async def handle_excel_file(update: Update, context: CallbackContext):
    """Обработчик загруженного файла Excel."""
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав для этой команды.")
        return

    document = update.message.document

    # Проверяем расширение файла
    if not document.file_name.endswith(".xlsx"):
        await update.message.reply_text("Ошибка: неверный тип файла. Пожалуйста, отправьте Excel-файл формата .xlsx.")
        return

    file = await document.get_file()

    # Создаем временный файл
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
        file_path = tmp_file.name
        await file.download_to_drive(file_path)

    try:
        # Читаем Excel-файл
        df = pd.read_excel(file_path)

        if {"Артикул", "Наименование", "Стоимость", "Ответственный"}.issubset(df.columns):
            # Обрабатываем полуфабрикаты
            await update.message.reply_text("Обнаружены данные о полуфабрикатах. Начинается загрузка...")
            await load_semi_finished_products(df, update)
        elif {"Название товара", "Артикул товара", "Состав", "Ответственный"}.issubset(df.columns):
            # Обрабатываем товары
            await update.message.reply_text("Обнаружены данные о товарах. Начинается загрузка...")
            await load_info_products(df, update)
        else:
            await update.message.reply_text("Ошибка: не удалось определить тип данных. Проверьте формат файла.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке файла: {str(e)}")

async def load_semi_finished_products(df, update):
    """Загрузка полуфабрикатов из DataFrame."""
    session = SessionLocal()
    for _, row in df.iterrows():
        article = str(row['Артикул'])
        name = str(row['Наименование'])
        cost = float(row['Стоимость'])
        responsible = str(row['Ответственный'])
        comment = str(row['Комментарий']) if 'Комментарий' in row else None

        # Проверяем, существует ли полуфабрикат
        existing_product = session.query(SemiFinishedProduct).filter_by(article=article).first()

        if existing_product:
            # Обновляем данные полуфабриката
            existing_product.name = name
            existing_product.cost = cost
            existing_product.responsible = responsible
            existing_product.comment = comment
        else:
            # Создаем новый полуфабрикат
            new_product = SemiFinishedProduct(
                article=article, name=name, cost=cost, responsible=responsible, comment=comment
            )
            session.add(new_product)

        session.commit()

    session.close()
    await update.message.reply_text("Данные о полуфабрикатах успешно загружены!")

async def load_info_products(df, update):
    """Загрузка товаров из DataFrame."""
    session = SessionLocal()
    for _, row in df.iterrows():
        product_article = str(row['Артикул товара'])
        product_name = str(row['Название товара'])
        composition_raw = str(row['Состав'])
        responsible = str(row['Ответственный'])
        comment = str(row['Комментарий']) if 'Комментарий' in row else None

        # Проверяем, существует ли товар
        existing_product = session.query(ProductComposition).filter_by(product_article=product_article).first()

        if existing_product:
            # Удаляем старый состав
            session.query(ProductComponent).filter_by(product_article=product_article).delete()
            # Обновляем данные товара
            existing_product.product_name = product_name
        else:
            # Создаем новый товар
            existing_product = ProductComposition(product_article=product_article, product_name=product_name)
            session.add(existing_product)

        session.commit()

        # Добавляем новый состав
        for item in composition_raw.split(";"):
            article, quantity = item.split(":")
            component = ProductComponent(
                product_article=product_article,
                semi_product_article=article.strip(),
                quantity=int(quantity.strip())
            )
            session.add(component)

        session.commit()

    session.close()
    await update.message.reply_text("Данные о товарах успешно загружены!")
