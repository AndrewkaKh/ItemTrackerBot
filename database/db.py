import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.config import DB_CONFIG

from database.models import Base


# Создание подключения через psycopg2
def get_psycopg2_connection():
    return psycopg2.connect(**DB_CONFIG)

# Создание движка SQLAlchemy с использованием psycopg2 подключения
engine = create_engine(
    "postgresql+psycopg2://",  # SQLAlchemy URI без указания строки подключения
    creator=get_psycopg2_connection,  # Функция для создания подключения
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Создание сессии для работы с базой данных.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def reset_database():
    """
    Пересоздает базу данных: удаляет все таблицы и создает их заново.
    """
    print("Сбрасываем базу данных...")
    Base.metadata.drop_all(bind=engine)  # Удаление всех таблиц
    Base.metadata.create_all(bind=engine)  # Создание всех таблиц заново
    print("База данных успешно сброшена и создана заново.")

def init_db():
    """
    Создаёт таблицы в базе данных, если они ещё не существуют.
    """
    print("🔧 Создаём таблицы в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы успешно созданы!")
