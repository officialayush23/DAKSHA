# app/api/routers/telegeram_webhook.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.models import TelegramUser, User
from app.integrations.telegram_client import send_telegram_message
import uuid

router = APIRouter(tags=["Integrations"])

@router.post("/webhooks/telegram")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    if "message" not in data: return {"status": "ok"}
    
    chat_id = str(data["message"]["chat"]["id"])
    text = data["message"].get("text", "")
    username = data["message"]["chat"].get("username")

    # Flow: User sends "/start <USER_UUID>"
    if text.startswith("/start"):
        parts = text.split(" ")
        if len(parts) == 2:
            user_uuid_str = parts[1]
            try:
                user_id = uuid.UUID(user_uuid_str)
                user = db.query(User).get(user_id)
                
                if user:
                    # Upsert Telegram User
                    tg_user = db.query(TelegramUser).filter_by(user_id=user_id).first()
                    if not tg_user:
                        tg_user = TelegramUser(
                            user_id=user_id,
                            chat_id=chat_id,
                            username=username,
                            opt_in=True
                        )
                        db.add(tg_user)
                    else:
                        tg_user.chat_id = chat_id # Update chat ID if changed
                    
                    db.commit()
                    
                    await send_telegram_message(
                        chat_id, 
                        f"✅ Successfully linked to **{user.name}**! You will receive order updates here."
                    )
                else:
                    await send_telegram_message(chat_id, "❌ User not found.")
            except ValueError:
                await send_telegram_message(chat_id, "❌ Invalid link format.")
        else:
            await send_telegram_message(chat_id, "👋 Welcome! Please use the link from the App to login.")

    return {"status": "ok"}