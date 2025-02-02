from sqlalchemy.orm import Session


from database.db import SessionLocal
from database.models import User



def fetch_all_users():
    db = SessionLocal()
    try:
        # Получение всех записей из таблицы users
        users = db.query(User).all()
        if not users:
            print("Таблица 'users' пуста.")
        else:
            for user in users:
                print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}, Expenses: {user.expenses}, Created At: {user.created_at}")
    except Exception as e:
        print(f"Ошибка при извлечении данных: {str(e)}")
    finally:
        db.close()

# Вызов функции
fetch_all_users()
