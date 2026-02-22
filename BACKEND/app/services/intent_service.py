# app/services/intent_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text

# for the agents to get recent user intent to personalize interactions, e.g. if user recently searched for "red dresses" we can use that signal to personalize the homepage feed or the recommendations shown in the chatbot


def get_recent_intent(db: Session, user_id: str):
    row = db.execute(text("""
        SELECT intent_text
        FROM user_intents
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT 1
    """), {"uid": user_id}).first()

    return row[0] if row else None