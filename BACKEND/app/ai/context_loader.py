# app/ai/context_loader.py
from sqlalchemy.orm import Session
from app.models.models import UserPreferenceSummary, ConversationSummary

def load_context(db: Session, user_id: str, session_id: str):
    pref = db.query(UserPreferenceSummary).filter_by(user_id=user_id).first()
    convo = db.query(ConversationSummary).filter_by(session_id=session_id).first()

    return {
        "user_summary": pref.summary_text if pref else None,
        "conversation_summary": convo.summary_text if convo else None,
    }