# app/services/telegram_service.py

from sqlalchemy.orm import Session
from app.models.models import TelegramUser, TelegramMessage
from app.models.models import User

def upsert_telegram_user(db: Session, user_id, chat_id: str):
    tg = db.query(TelegramUser).filter_by(user_id=user_id).first()

    if tg:
        tg.chat_id = chat_id
        tg.opt_in = True
    else:
        tg = TelegramUser(
            user_id=user_id,
            chat_id=chat_id,
            opt_in=True,
        )
        db.add(tg)

    db.commit()
    return tg


def log_telegram_message(
    db: Session,
    user_id,
    chat_id: str,
    direction: str,
    message: str,
    status: str = "sent",
):
    msg = TelegramMessage(
        user_id=user_id,
        chat_id=chat_id,
        direction=direction,
        message=message,
        status=status,
    )
    db.add(msg)
    db.commit()


def find_user_by_phone_or_email(db: Session, telegram_payload: dict):
    """
    VERY IMPORTANT:
    Telegram gives you:
      - username
      - first_name
      - phone ONLY if user shares contact
    We match ONLY if:
      - phone shared OR
      - username already mapped elsewhere
    """

    msg = telegram_payload.get("message", {})
    contact = msg.get("contact")

    if contact and contact.get("phone_number"):
        phone = contact["phone_number"]
        return db.query(User).filter(User.phone == phone).first()

    return None  # do NOT auto-create users here
