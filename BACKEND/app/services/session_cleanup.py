# app/services/session_cleanup.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import UserSession

SESSION_TTL_HOURS = 12

def expire_sessions(db: Session):
    cutoff = datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)

    sessions = (
        db.query(UserSession)
        .filter(UserSession.ended_at.is_(None))
        .filter(UserSession.started_at < cutoff)
        .all()
    )

    for s in sessions:
        s.ended_at = datetime.utcnow()

    db.commit()
