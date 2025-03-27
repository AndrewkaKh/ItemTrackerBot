from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2

from bot.config import DB_CONFIG
from database.models import Base




def get_psycopg2_connection():
    return psycopg2.connect(**DB_CONFIG)

engine = create_engine(
    "postgresql+psycopg2://",
    creator=get_psycopg2_connection,
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
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("База данных успешно сброшена и создана заново.")

def init_db():
    """
    Создаёт таблицы в базе данных, если они ещё не существуют.
    """
    print("🔧 Создаём таблицы в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы успешно созданы!")
