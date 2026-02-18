# app/services/session_service.py
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import UserSession
from app.enums.db_enums import ChannelEnum


def get_active_session(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> UserSession | None:
    return (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.ended_at.is_(None),
        )
        .order_by(UserSession.started_at.desc())
        .first()
    )


def start_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    channel: ChannelEnum,
) -> UserSession:
    """
    Logged-in users always have exactly ONE active session.
    We never end it. We only reuse it.
    """

    session = get_active_session(db, user_id=user_id)
    if session:
        # Just sync channel
        if session.active_channel != channel:
            session.active_channel = channel
            db.commit()
        return session

    session = UserSession(
        user_id=user_id,
        primary_channel=channel,
        active_channel=channel,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def switch_channel(
    db: Session,
    *,
    session: UserSession,
    channel: ChannelEnum,
):
    if session.active_channel != channel:
        session.active_channel = channel
        db.commit()
