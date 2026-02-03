# app/services/checkout_notifications.py

from sqlalchemy.orm import Session
from app.integrations.telegram_client import send_telegram_message
from app.models.models import TelegramUser

async def notify_payment_failed(db: Session, user_id, checkout_id, reason: str):
    tg = db.query(TelegramUser).filter_by(user_id=user_id, opt_in=True).first()
    if not tg:
        return

    await send_telegram_message(
        chat_id=tg.chat_id,
        text=(
            "*Payment Failed*\n"
            f"Reason: {reason}\n\n"
            "You can retry without losing your reservation."
        ),
        buttons=[[
            {
                "text": "Retry Payment",
                "url": f"https://daksha.com/checkout/{checkout_id}"
            }
        ]]
    )

async def notify_order_confirmed(db: Session, order):
    tg = db.query(TelegramUser).filter_by(user_id=order.user_id, opt_in=True).first()
    if not tg:
        return

    await send_telegram_message(
        tg.chat_id,
        f"*Order Confirmed* 🎉\nOrder #{order.id}",
        buttons=[[
            {
                "text": "View Order",
                "url": f"https://daksha.com/orders/{order.id}"
            }
        ]]
    )
