# app/services/telegram_onboarding.py
from sqlalchemy.orm import Session
from app.models.models import TelegramUser, User

def handle_start(db: Session, chat_id: str, payload: dict):
    username = payload["message"]["from"].get("username")
    if not username:
        return None

    user = db.query(User).filter(User.email == username).first()
    if not user:
        return None

    tg = TelegramUser(
        user_id=user.id,
        chat_id=chat_id,
        opt_in=True
    )
    db.merge(tg)
    db.commit()
    return user
