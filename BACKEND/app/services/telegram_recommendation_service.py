# app/services/telegram_recommendation_service.py
from sqlalchemy.orm import Session

from app.services.recommendation_service import recommend
from app.services.trending_service import get_trending_feed
from app.services.telegram_notification_service import send_telegram_and_log


async def send_daily_recommendations(db: Session, user_id: str):
    """Daily picks to the user's linked Telegram chat (no-op if not linked)."""
    recs = recommend(db, user_id, None, limit=5, feed_type="telegram")
    trending = get_trending_feed(db, user_id, limit=5)
    lines = ["🔥 *Daily picks for you*", ""] + [f"• {r['name']} — ₹{r['final_price']:.0f}" for r in recs]
    lines += ["", "📈 *Trending now*", ""] + [f"• {t['name']} — ₹{t['final_price']:.0f}" for t in trending]
    return await send_telegram_and_log(db, user_id=user_id, text="\n".join(lines), message_type="daily_recommendations")
