from datetime import datetime
from itertools import product

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

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
                "Неверный формат аргументов.\nФормат: /add_item <Артикул>;<Название>;<Стоимость>;<Ответственный>\nПример: /add_item 123;Название;100;Ответственный"
            )
            return

        parts = args.split(";")
        if len(parts) < 4:
            await update.message.reply_text(
                "Неверное количество аргументов.\nФормат: /add_item <Артикул>;<Название>;<Стоимость>;<Ответственный>\nПример: /add_item 123;Название;100;Ответственный"
            )
            return

        article, name, cost, responsible = parts[0].strip(), parts[1].strip(), float(parts[2].strip()), parts[3].strip()

        db = SessionLocal()
        new_item = SemiFinishedProduct(article=article, name=name, cost=cost, responsible=responsible)
        db.add(new_item)
        db.commit()
        db.close()

        await update.message.reply_text(f"Полуфабрикат '{name}' успешно добавлен!")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

@require_auth
async def movement_from(update: Update, context: CallbackContext):
    """
    Команда для отслеживания отправки товаров со склада.
    Пример: /ot <артикул>;<количество>[;комментарий]
    """
    try:
        username = update.effective_user.username
        args = " ".join(context.args)
        if ";" not in args:
            await update.message.reply_text(
                "Неверный формат аргументов.\nФормат: /ot <артикул>; <количество>; <комментарий>\nПример: /ot 12345; 10; Комментарий"
            )
            return

        parts = args.split(";")
        if len(parts) < 2:
            await update.message.reply_text(
                "Неверное количество аргументов.\nФормат: /ot <артикул>; <количество>; <комментарий>\nПример: /ot 12345; 10; Комментарий"
            )
            return

        article, outgoing = parts[0].strip(), int(parts[1].strip())
        comment = parts[2].strip() if len(parts) > 2 else ""

        db = SessionLocal()

        semi_product = db.query(SemiFinishedProduct).filter_by(article=article).first()

        product = db.query(ProductComposition).filter_by(product_article=article).first()

        current_date = datetime.now()

        if semi_product:
            movement_entry = Movement(
                date=current_date,
                article=article,
                name=semi_product.name,
                incoming=0,
                outgoing=outgoing,
                comment=comment,
            )
            db.add(movement_entry)

            stock_entry = db.query(Stock).filter_by(article=article).first()
            if not stock_entry:
                stock_entry = Stock(
                    article=article,
                    name=semi_product.name,
                    in_stock=-outgoing,
                    cost=semi_product.cost,
                )
                db.add(stock_entry)
            else:
                stock_entry.in_stock -= outgoing

            if stock_entry.in_stock < 0:
                await update.message.reply_text(
                    f"Ошибка: остаток полуфабриката '{semi_product.name}' стал отрицательным. Проверьте данные."
                )
                db.rollback()
                db.close()
                return

            db.commit()
            await update.message.reply_text(f"Отгрузка полуфабриката '{semi_product.name}' произведена.")

        elif product:
            stock_entry = db.query(Stock).filter_by(article=article).first()
            if stock_entry:
                if stock_entry.in_stock >= outgoing:
                    stock_entry.in_stock -= outgoing
                    movement_entry = Movement(
                        date=current_date,
                        article=article,
                        name=product.product_name,
                        incoming=0,
                        outgoing=outgoing,
                        comment=comment,
                    )
                    db.add(stock_entry)
                    db.add(movement_entry)
                else:
                    await update.message.reply_text(
                        f"Товар '{product.product_name}' доступен в количестве: {stock_entry.in_stock}, не хватает {outgoing - stock_entry.in_stock}."
                    )
                    db.close()
                    return
            else:
                await update.message.reply_text(
                    f"Товара '{product.product_name}' нет на складе."
                )
                db.close()
                return
            db.commit()
            await update.message.reply_text(f"Отгрузка товара '{product.product_name}' произведена.")
        else:
            await update.message.reply_text(f"Ошибка: артикул '{article}' не найден.")

        db.close()
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


@require_auth
async def movement_to(update: Update, context: CallbackContext):
    """
    Команда для отслеживания поступления товара на склад.
    Пример: /po <артикул>;<количество>[;комментарий]
    """
    try:
        username = update.effective_user.username
        args = " ".join(context.args)
        if ";" not in args:
            await update.message.reply_text(
                "Неверный формат аргументов.\nФормат: /po <артикул>; <количество>; <комментарий>\nПример: /po 12345; 10; Комментарий"
            )
            return

        parts = args.split(";")
        if len(parts) < 2:
            await update.message.reply_text(
                "Неверное количество аргументов.\nФормат: /po <артикул>; <количество>; <комментарий>\nПример: /po 12345; 10; Комментарий"
            )
            return

        article, incoming = parts[0].strip(), int(parts[1].strip())
        comment = parts[2].strip() if len(parts) > 2 else ""

        db = SessionLocal()

        semi_product = db.query(SemiFinishedProduct).filter_by(article=article).first()

        product = db.query(ProductComposition).filter_by(product_article=article).first()

        current_date = datetime.now()

        if semi_product:
            movement_entry = Movement(
                date=current_date,
                article=article,
                name=semi_product.name,
                incoming=incoming,
                outgoing=0,
                comment=comment,
            )
            db.add(movement_entry)

            stock_entry = db.query(Stock).filter_by(article=article).first()
            if not stock_entry:
                stock_entry = Stock(
                    article=article,
                    name=semi_product.name,
                    in_stock=incoming,
                    cost=semi_product.cost*incoming,
                )
                db.add(stock_entry)
            else:
                stock_entry.in_stock += incoming
                stock_entry.cost += incoming*semi_product.cost

            stock_pay_user = db.query(User).filter_by(username=username).first()
            stock_pay_user.expenses -= incoming * semi_product.cost

            db.commit()
            await update.message.reply_text(f"Поступление полуфабриката '{semi_product.name}' произведено.")
            db.close()
            return

        elif product:
            await update.message.reply_text(f"Товар '{product.product_name}' может только отгружаться со склада.")

        else:
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
                "Неверный формат.\nФормат: /add_product <Название товара>;<Артикул товара>;<Состав: Артикул1:Кол-во,Артикул2:Кол-во>\nПример: /add_product Название товара;Артикул товара;Артикул1:10,Артикул2:20"
            )
            return

        parts = args.split(";")
        if len(parts) != 3:
            await update.message.reply_text(
                "Неверный формат.\nФормат: /add_product <Название товара>;<Артикул товара>;<Состав: Артикул1:Кол-во,Артикул2:Кол-во>\nПример: /add_product Название товара;Артикул товара;Артикул1:10,Артикул2:20"
            )
            return

        product_name = parts[0].strip()
        product_article = parts[1].strip()
        composition_raw = parts[2].strip()

        db = SessionLocal()

        existing_product = db.query(ProductComposition).filter_by(product_article=product_article).first()
        if existing_product:
            await update.message.reply_text(
                f"Товар с артикулом '{product_article}' уже существует: {existing_product.product_name}."
            )
            db.close()
            return

        composition = []
        for item in composition_raw.split(","):
            article, qty = item.split(":")
            composition.append({"article": article.strip(), "quantity": int(qty)})

        for component in composition:
            semi_product = db.query(SemiFinishedProduct).filter_by(article=component["article"]).first()
            if not semi_product:
                await update.message.reply_text(
                    f"Полуфабрикат с артикулом '{component['article']}' не найден. Добавьте его перед использованием."
                )
                db.close()
                return

        new_product = ProductComposition(product_article=product_article, product_name=product_name)
        db.add(new_product)
        db.commit()

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
    Пример: /del_article <артикул>
    """
    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Неверное количество аргументов.\nФормат: /del_article <артикул>\nПример: /del_article 12345")
            return

        article = args[0].strip()
        db = SessionLocal()

        product = db.query(ProductComposition).filter_by(product_article=article).first()
        if product:
            db.query(ProductComponent).filter_by(product_article=article).delete()
            db.delete(product)
            db.query(Stock).filter_by(article=article).delete()
            db.commit()
            await update.message.reply_text(f"Товар с артикулом '{article}' успешно удален.")
            db.close()
            return

        semi_product = db.query(SemiFinishedProduct).filter_by(article=article).first()
        if semi_product:
            product_component = db.query(ProductComponent).filter_by(semi_product_article=article).first()
            if product_component:
                await update.message.reply_text(
                    f"Нельзя удалить полуфабрикат с артикулом '{article}', так как он используется в составе товара.")
                db.close()
                return

            db.query(Stock).filter_by(article=article).delete()
            db.query(Movement).filter_by(article=article).delete()
            db.delete(semi_product)
            db.commit()
            await update.message.reply_text(f"Полуфабрикат с артикулом '{article}' успешно удален.")
            db.close()
            return

        await update.message.reply_text(f"Ошибка: артикул '{article}' не найден.")
        db.close()
    except Exception as e:
        await update.message.reply_text(f"Ошибка при удалении артикула: {str(e)}")

@require_auth
async def production(update: Update, context: CallbackContext):
    """
    Команда для конвертации полуфабрикатов в товары.
    Пример: /pr <Артикул>; <Количество>
    """

    try:
        args = " ".join(context.args)
        if ";" not in args:
            await update.message.reply_text(
                "Неверный формат.\nФормат: /pr <Артикул>; <Количество>\nПример: /pr FS_ST005; 2"
            )
            return

        parts = args.split(";")
        if len(parts) != 2:
            await update.message.reply_text(
                "Неверное количество аргументов.\nФормат: /pr <Артикул>; <Количество>\nПример: /pr FS_ST005; 2"
            )
            return

        current_date = datetime.now()
        article = parts[0].strip()
        quantity = int(parts[1].strip())

        db = SessionLocal()
        product_exist = db.query(ProductComposition).filter_by(product_article=article).first()
        if product_exist:
            components = db.query(ProductComponent).filter_by(product_article=article).all()
            if not components:
                await update.message.reply_text(f"Ошибка: для товара '{product_exist.product_name}' не задан состав.")
                db.close()
                return

            insufficient_components = []
            for component in components:
                stock_entry = db.query(Stock).filter_by(article=component.semi_product_article).first()
                if not stock_entry or stock_entry.in_stock < component.quantity * quantity:
                    insufficient_components.append((stock_entry, component))

            if insufficient_components:
                missing_items = ", ".join(
                    [
                        f"{c[1].semi_product_article} (нужно: {c[1].quantity * quantity}, есть: {c[0].in_stock if c[0] else 0})"
                        for c in insufficient_components
                    ]
                )
                await update.message.reply_text(
                    f"Нельзя произвести товар '{product_exist.product_name}' в количестве {quantity}.\n"
                    f"Не хватает полуфабрикатов: {missing_items}"
                )
                db.close()
                return

            for component in components:
                stock_entry = db.query(Stock).filter_by(article=component.semi_product_article).first()
                stock_entry.cost = stock_entry.cost / stock_entry.in_stock
                stock_entry.in_stock -= component.quantity * quantity
                stock_entry.cost *= stock_entry.in_stock

            movement_entry = Movement(
                date=current_date,
                article=article,
                name=product_exist.product_name,
                incoming=0,
                outgoing=quantity,
                comment=f"Производство товара",
            )

            stock_entry = db.query(Stock).filter_by(article=article).first()
            if not stock_entry:
                stock_entry = Stock(
                    article=article,
                    name=product_exist.product_name,
                    in_stock=quantity,
                    cost=0,
                )
                db.add(stock_entry)
            else:
                stock_entry.in_stock += quantity
            db.add(movement_entry)
            db.commit()
            await update.message.reply_text(
                f"Успешно произвели товар: '{product_exist.product_name}' в количестве: {quantity}"
            )
        else:
            await update.message.reply_text("Производить можно только товары (возможно товар не зарегистрирован в системе).")

        db.close()
    except Exception as e:
        await update.message.reply_text(f"Ошибка при производстве товара: {str(e)}")