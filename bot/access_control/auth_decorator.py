from functools import wraps

from bot.config import ADMIN_ID
from database.db import SessionLocal
from database.models import User


def require_auth(func):
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        db = SessionLocal()
        username = update.effective_user.username
        user = db.query(User).filter_by(username=username).first()
        db.close()

        if update.effective_user.id != int(ADMIN_ID) and not user:
            await update.message.reply_text("Доступ запрещен. Пожалуйста, свяжитесь с администратором.")
            return
        return await func(update, context, *args, **kwargs)

    return wrapper
