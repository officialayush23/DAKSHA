# app/services/telegram_recommendation_service.py
import requests
from sqlalchemy.orm import Session
from app.services.recommendation_service import get_hybrid_recommendations
from app.services.trending_service import get_trending_feed

TELEGRAM_BOT_TOKEN = "YOUR_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"


def _send_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })


def send_daily_recommendations(db: Session, user_id: str):
    recs = get_hybrid_recommendations(db, user_id, limit=5)
    trending = get_trending_feed(db, user_id, limit=5)

    message = "🔥 *Daily Picks For You*\n\n"

    for r in recs:
        message += f"• {r['name']} — ₹{r['final_price']}\n"

    message += "\n📈 *Trending Now*\n\n"

    for t in trending:
        message += f"• {t['name']} — ₹{t['final_price']}\n"

    _send_message(message)