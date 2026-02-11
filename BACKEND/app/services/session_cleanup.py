# app/services/session_cleanup.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import UserSession

# Constants matching your Postgres Cron Job
SESSION_TTL_ANON_HOURS = 24
SESSION_TTL_AUTH_HOURS = 168  # 7 days

def expire_sessions(db: Session):
    """
    Python fallback for session cleanup. 
    Useful for development or if the Cron job fails.
    """
    now = datetime.utcnow()
    
    # 1. Expire Anonymous Sessions > 24h
    anon_cutoff = now - timedelta(hours=SESSION_TTL_ANON_HOURS)
    db.query(UserSession).filter(
        UserSession.ended_at.is_(None),
        UserSession.user_id.is_(None),
        UserSession.started_at < anon_cutoff
    ).update({UserSession.ended_at: now}, synchronize_session=False)

    # 2. Expire Authenticated Sessions > 7 days
    auth_cutoff = now - timedelta(hours=SESSION_TTL_AUTH_HOURS)
    db.query(UserSession).filter(
        UserSession.ended_at.is_(None),
        UserSession.user_id.is_not(None),
        UserSession.started_at < auth_cutoff
    ).update({UserSession.ended_at: now}, synchronize_session=False)

    db.commit()