# app/api/routers/telegram.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.services.telegram_service import (
    upsert_telegram_user,
    log_telegram_message,
    find_user_by_phone_or_email,
)
from app.services.telegram_onboarding import handle_start
router = APIRouter(prefix="/telegram", tags=["Telegram"])

@router.post("/webhook")
async def telegram_webhook(payload: dict, db: Session = Depends(get_db)):
    msg = payload.get("message")
    if not msg:
        return {"ok": True}

    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "")
    if text == "/start":
        handle_start(db, chat_id, payload)
        return {"ok": True}

    user = find_user_by_phone_or_email(db, payload)
    if not user:
        return {"ok": True}  # ignore unlinked users

    upsert_telegram_user(db, user.id, chat_id)

    log_telegram_message(
        db=db,
        user_id=user.id,
        chat_id=chat_id,
        direction="inbound",
        message=text,
        status="received",
    )

    return {"ok": True}



