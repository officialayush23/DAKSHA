# app/services/session_service.py
import uuid
from sqlalchemy.orm import Session
from app.models.models import UserSession
from app.enums.db_enums import ChannelEnum
from datetime import datetime

def get_active_session(db: Session, user_id: uuid.UUID):
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.ended_at.is_(None))
        .first()
    )

def start_session(db: Session, user_id: uuid.UUID, channel: ChannelEnum):
    existing = get_active_session(db, user_id)
    if existing:
        return existing

    session = UserSession(
        user_id=user_id,
        primary_channel=channel,
        active_channel=channel,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def switch_channel(db: Session, session: UserSession, channel: ChannelEnum):
    session.active_channel = channel
    db.commit()
    return session

def end_session(db: Session, session: UserSession):
    session.ended_at = datetime.utcnow()
    db.commit()

def get_or_create_active_session(
    db: Session,
    user_id: uuid.UUID,
    channel: ChannelEnum,
):
    """
    HARD GUARANTEE:
    - If user does anything, they have a session
    - Channel is always up to date
    """
    session = get_active_session(db, user_id)

    if session:
        if session.active_channel != channel:
            session.active_channel = channel
            db.commit()
        return session

    return start_session(db, user_id, channel)