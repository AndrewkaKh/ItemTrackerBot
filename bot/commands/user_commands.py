from datetime import datetime

from telegram.ext import CommandHandler, CallbackContext
from telegram import Update

from bot.access_control.auth_decorator import require_auth
from database.db import SessionLocal
from database.models import SemiFinishedProduct, Movement, Stock, ProductComposition, ProductComponent, User

@require_auth
async def add_item(update: Update, context: CallbackContext):
    """
    Команда для добавления полуфабриката.
    Пример использования:
    /add_item <Артикул>;<Название>;<Стоимость>;<Ответственный>
    """
    try:
        args = " ".join(context.args)
        if ";" not in args:
            await update.message.reply_text(
                "Неверный формат аргументов.\nПример: /add_item 123;Название;100;Ответственный"
            )
            return

        parts = args.split(";")
        if len(parts) < 4:
            await update.message.reply_text(
                "Неверное количество аргументов.\nПример: /add_item 123;Название;100;Ответственный"
            )
            return

        article, name, cost, responsible = parts[0].strip(), parts[1].strip(), float(parts[2].strip()), parts[3].strip()

        # Сохраняем полуфабрикат в базу данных
        db = SessionLocal()
        new_item = SemiFinishedProduct(article=article, name=name, cost=cost, responsible=responsible)
        db.add(new_item)
        db.commit()
        db.close()

        await update.message.reply_text(f"Полуфабрикат '{name}' успешно добавлен!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

@require_auth
async def movement(update: Update, context: CallbackContext):
    """
    Команда для добавления движения товаров.
    Пример: /movement <артикул>;<поступление>;<отгрузка>[;комментарий]
    """
    try:
        username = update.effective_user.username
        args = " ".join(context.args)
        if ";" not in args:
            await update.message.reply_text(
                "Неверный формат аргументов.\nПример: /movement 12345;10;5;Комментарий"
            )
            return

        parts = args.split(";")
        if len(parts) < 3:
            await update.message.reply_text(
                "Неверное количество аргументов.\nПример: /movement 12345;10;5;Комментарий"
            )
            return

        article, incoming, outgoing = parts[0].strip(), int(parts[1].strip()), int(parts[2].strip())
        comment = parts[3].strip() if len(parts) > 3 else ""

        db = SessionLocal()

        # Проверяем, является ли артикул полуфабрикатом
        semi_product = db.query(SemiFinishedProduct).filter_by(article=article).first()

        # Проверяем, является ли артикул товаром
        product = db.query(ProductComposition).filter_by(product_article=article).first()

        current_date = datetime.now()  # Получаем текущую дату и время

        if semi_product:
            # Добавляем запись о движении полуфабриката
            movement_entry = Movement(
                date=current_date,
                article=article,
                name=semi_product.name,
                incoming=incoming,
                outgoing=outgoing,
                comment=comment,
            )
            db.add(movement_entry)

            # Обновляем остаток полуфабриката
            stock_entry = db.query(Stock).filter_by(article=article).first()
            if not stock_entry:
                stock_entry = Stock(
                    article=article,
                    name=semi_product.name,
                    in_stock=incoming - outgoing,
                    cost=semi_product.cost,
                )
                db.add(stock_entry)
            else:
                stock_entry.in_stock += incoming - outgoing

            if stock_entry.in_stock < 0:
                await update.message.reply_text(
                    f"Ошибка: остаток полуфабриката '{semi_product.name}' стал отрицательным. Проверьте данные."
                )
                db.rollback()
                db.close()
                return

            stock_pay_user = db.query(User).filter_by(username=username).first()
            stock_pay_user.expenses -= incoming * semi_product.cost

            db.commit()
            await update.message.reply_text(f"Движение для полуфабриката '{semi_product.name}' успешно добавлено.")
            db.close()
            return

        elif product:
            # Если это товар, обновляем остатки для всех полуфабрикатов
            components = db.query(ProductComponent).filter_by(product_article=article).all()
            if not components:
                await update.message.reply_text(f"Ошибка: для товара '{product.product_name}' не задан состав.")
                db.close()
                return

            # Проверяем, достаточно ли полуфабрикатов для отгрузки
            insufficient_components = []
            for component in components:
                stock_entry = db.query(Stock).filter_by(article=component.semi_product_article).first()
                if not stock_entry or stock_entry.in_stock < component.quantity * outgoing:
                    insufficient_components.append(component)

            if insufficient_components:
                missing_items = ", ".join(
                    [
                        f"{c.semi_product_article} (нужно: {c.quantity * outgoing}, есть: {stock_entry.in_stock if stock_entry else 0})"
                        for c in insufficient_components
                    ]
                )
                await update.message.reply_text(
                    f"Нельзя отгрузить товар '{product.product_name}' в количестве {outgoing}.\n"
                    f"Не хватает полуфабрикатов: {missing_items}"
                )
                db.close()
                return

            # Обновляем остатки для всех полуфабрикатов
            for component in components:
                stock_entry = db.query(Stock).filter_by(article=component.semi_product_article).first()
                stock_entry.in_stock -= component.quantity * outgoing

            # Логируем движение товара
            movement_entry = Movement(
                date=current_date,
                article=article,
                name=product.product_name,
                incoming=incoming,
                outgoing=outgoing,
                comment=comment,
            )
            db.add(movement_entry)
            db.commit()
            await update.message.reply_text(f"Движение товара '{product.product_name}' успешно добавлено.")

        else:
            # Если артикул не найден
            await update.message.reply_text(f"Ошибка: артикул '{article}' не найден.")
            db.close()
            return

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

@require_auth
async def add_product(update: Update, context: CallbackContext):
    """
    Команда для добавления состава товара.
    Пример использования:
    /add_product <Название товара>;<Артикул товара>;<Состав: Артикул1:Кол-во,Артикул2:Кол-во>
    """
    try:
        args = " ".join(context.args)
        if ";" not in args:
            await update.message.reply_text(
                "Неверный формат. Пример:\n/add_product Название товара;Артикул товара;Артикул1:10,Артикул2:20"
            )
            return

        # Разбираем данные
        parts = args.split(";")
        if len(parts) != 3:
            await update.message.reply_text(
                "Неверный формат. Пример:\n/add_product Название товара;Артикул товара;Артикул1:10,Артикул2:20"
            )
            return

        product_name = parts[0].strip()
        product_article = parts[1].strip()
        composition_raw = parts[2].strip()

        db = SessionLocal()

        # Проверяем, существует ли товар с данным артикулом
        existing_product = db.query(ProductComposition).filter_by(product_article=product_article).first()
        if existing_product:
            await update.message.reply_text(
                f"Товар с артикулом '{product_article}' уже существует: {existing_product.product_name}."
            )
            db.close()
            return

        # Парсим состав
        composition = []
        for item in composition_raw.split(","):
            article, qty = item.split(":")
            composition.append({"article": article.strip(), "quantity": int(qty)})

        # Проверяем наличие полуфабрикатов
        for component in composition:
            semi_product = db.query(SemiFinishedProduct).filter_by(article=component["article"]).first()
            if not semi_product:
                await update.message.reply_text(
                    f"Полуфабрикат с артикулом '{component['article']}' не найден. Добавьте его перед использованием."
                )
                db.close()
                return

        # Сохраняем товар
        new_product = ProductComposition(product_article=product_article, product_name=product_name)
        db.add(new_product)
        db.commit()

        # Добавляем состав
        for component in composition:
            product_component = ProductComponent(
                product_article=product_article,
                semi_product_article=component["article"],
                quantity=component["quantity"],
            )
            db.add(product_component)
            print(f"Добавляется компонент: {component['article']} (количество: {component['quantity']})")
        db.commit()
        db.close()

        await update.message.reply_text(f"Товар '{product_name}' с артикулом '{product_article}' успешно добавлен!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении товара: {str(e)}")

@require_auth
async def del_article(update: Update, context: CallbackContext):
    """
    Команда для удаления артикула (товара или полуфабриката).
    Пример: /delete <артикул>
    """
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Неверное количество аргументов. Пример: /delete 12345")
            return

        article = args[0].strip()
        db = SessionLocal()

        # Проверяем, является ли артикул товаром
        product = db.query(ProductComposition).filter_by(product_article=article).first()
        if product:
            # Удаляем состав товара
            db.query(ProductComponent).filter_by(product_article=article).delete()
            # Удаляем сам товар
            db.delete(product)
            db.commit()
            await update.message.reply_text(f"Товар с артикулом '{article}' успешно удален.")
            db.close()
            return

        # Проверяем, является ли артикул полуфабрикатом
        semi_product = db.query(SemiFinishedProduct).filter_by(article=article).first()
        if semi_product:
            # Удаляем остатки полуфабриката
            db.query(Stock).filter_by(article=article).delete()
            # Удаляем записи о движении полуфабриката
            db.query(Movement).filter_by(article=article).delete()
            # Удаляем сам полуфабрикат
            db.delete(semi_product)
            db.commit()
            await update.message.reply_text(f"Полуфабрикат с артикулом '{article}' успешно удален.")
            db.close()
            return

        # Если артикул не найден
        await update.message.reply_text(f"Ошибка: артикул '{article}' не найден.")
        db.close()
    except Exception as e:
        await update.message.reply_text(f"Ошибка при удалении артикула: {str(e)}")
