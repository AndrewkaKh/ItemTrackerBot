from telegram.ext import CommandHandler, CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from database.db import reset_database, SessionLocal

from bot.config import ADMIN_ID
from database.models import User


async def reset_db(update: Update, context: CallbackContext):
    """
    Команда для сброса базы данных (пересоздание таблиц).
    Выводит предупреждение с кнопками подтверждения и отмены.
    """
    try:
        if str(update.effective_user.id) != ADMIN_ID:
            await update.message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        # Кнопки подтверждения и отмены
        keyboard = [
            [
                InlineKeyboardButton("Подтверждаю", callback_data="confirm_reset_db"),
                InlineKeyboardButton("Отмена", callback_data="cancel_reset_db"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Сообщение с предупреждением
        await update.message.reply_text(
            "⚠️ ВНИМАНИЕ: Эта операция полностью очистит базу данных, включая все записи о движении товаров за все время. "
            "Вы уверены, что хотите продолжить?",
            reply_markup=reply_markup,
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


async def confirm_reset_db(update: Update, context: CallbackContext):
    """
    Функция, выполняющая сброс базы данных после подтверждения.
    """
    try:
        # Подтверждение от администратора
        query = update.callback_query
        if str(query.from_user.id) != ADMIN_ID:
            await query.answer("У вас нет прав для выполнения этой команды.", show_alert=True)
            return

        # Сброс базы данных
        reset_database()

        await query.edit_message_text("✅ База данных успешно сброшена! Все данные удалены.")
    except Exception as e:
        await query.edit_message_text(f"Ошибка при сбросе базы данных: {str(e)}")


async def cancel_reset_db(update: Update, context: CallbackContext):
    """
    Функция для обработки отмены сброса базы данных.
    """
    try:
        # Отмена от администратора
        query = update.callback_query
        if str(query.from_user.id) != ADMIN_ID:
            await query.answer("У вас нет прав для выполнения этой команды.", show_alert=True)
            return

        # Уведомление об отмене действия
        await query.edit_message_text("❌ Сброс базы данных отменен.")
    except Exception as e:
        await query.edit_message_text(f"Ошибка при отмене сброса базы данных: {str(e)}")


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

        await update.message.reply_text(
            f"На счет пользователя {username} зачислено {amount} единиц. "
            f"Новый баланс: {user.expenses}."
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
    finally:
        db.close()
