from sqlalchemy.orm import Session
from database.models import Movement


def apply_filter(db: Session, start_date: str, end_date: str):
    """
    Фильтрация данных по дате.
    :param db: Сессия базы данных
    :param start_date: Начальная дата в формате YYYY-MM-DD
    :param end_date: Конечная дата в формате YYYY-MM-DD
    :return: Список отфильтрованных записей
    """
    try:
        query = db.query(Movement).filter(Movement.date >= start_date, Movement.date <= end_date).all()
        return query
    except Exception as e:
        raise ValueError(f"Ошибка фильтрации: {str(e)}")
