# app/services/session_service.py
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.models import UserSession, Cart, Event, UserIntent, UserEngagementEvent
from app.enums.db_enums import ChannelEnum

def get_active_session(db: Session, user_id: uuid.UUID = None, anonymous_id: uuid.UUID = None):
    query = db.query(UserSession).filter(UserSession.ended_at.is_(None))
    
    if user_id:
        query = query.filter(UserSession.user_id == user_id)
    elif anonymous_id:
        query = query.filter(UserSession.anonymous_id == anonymous_id)
    else:
        return None
        
    # Get the most recent active session
    return query.order_by(UserSession.started_at.desc()).first()

def expire_old_sessions(db: Session, user_id: uuid.UUID = None, anonymous_id: uuid.UUID = None):
    """
    Soft-closes any other open sessions for this specific identity 
    to ensure we only have one 'primary' active session context.
    """
    query = db.query(UserSession).filter(UserSession.ended_at.is_(None))
    
    if user_id:
        query = query.filter(UserSession.user_id == user_id)
    elif anonymous_id:
        query = query.filter(UserSession.anonymous_id == anonymous_id)
    else:
        return

    # Bulk update is faster
    query.update({UserSession.ended_at: datetime.utcnow()}, synchronize_session=False)
    db.commit()

def start_session(db: Session, user_id: uuid.UUID = None, anonymous_id: uuid.UUID = None, channel: ChannelEnum = ChannelEnum.web):
    # Close any stale/concurrent sessions first to maintain 1 active session constraint
    expire_old_sessions(db, user_id, anonymous_id)

    session = UserSession(
        user_id=user_id,
        anonymous_id=anonymous_id,
        primary_channel=channel,
        active_channel=channel,
        started_at=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_or_create_active_session(
    db: Session, 
    user_id: uuid.UUID = None, 
    anonymous_id: uuid.UUID = None, 
    channel: ChannelEnum = ChannelEnum.web
):
    """
    The Single Source of Truth for accessing the current user state.
    Handles channel switching (Web -> Kiosk) without killing the session.
    """
    session = get_active_session(db, user_id, anonymous_id)
    
    if session:
        # If channel changed (e.g. user moved from App to Kiosk), update it
        # This keeps the session ID and Context (Chat History) alive!
        if session.active_channel != channel:
            session.active_channel = channel
            db.commit()
            db.refresh(session)
        return session
        
    return start_session(db, user_id, anonymous_id, channel)

def merge_anonymous_session(db: Session, anonymous_id: uuid.UUID, user_id: uuid.UUID):
    """
    CRITICAL: Transfers Guest History -> Logged-in User.
    1. Finds the active guest session.
    2. Assigns it to the user.
    3. Moves Cart, Events, and Intents.
    """
    # 1. Find active anonymous session
    anon_session = get_active_session(db, anonymous_id=anonymous_id)
    
    if not anon_session:
        return None

    # 2. Convert Session Ownership
    # We essentially "promote" the anonymous session to be the user's session
    anon_session.user_id = user_id
    anon_session.anonymous_id = None 
    
    # Close any OTHER sessions the user might have left open previously
    # so this newly merged session becomes the master.
    db.query(UserSession).filter(
        UserSession.user_id == user_id, 
        UserSession.id != anon_session.id,
        UserSession.ended_at.is_(None)
    ).update({UserSession.ended_at: datetime.utcnow()}, synchronize_session=False)

    # 3. Reassign Events (Tracking)
    db.query(Event).filter(Event.anonymous_id == anonymous_id).update(
        {"user_id": user_id, "anonymous_id": None}, synchronize_session=False
    )

    # 4. Reassign Carts
    # Only reassign if the user doesn't have a newer cart? 
    # For now, we take the guest cart and assign it to the user.
    db.query(Cart).filter(Cart.session_id == anon_session.id).update(
        {"user_id": user_id}, synchronize_session=False
    )

    # 5. Reassign Intents (Chat History Context)
    db.query(UserIntent).filter(UserIntent.session_id == anon_session.id).update(
        {"user_id": user_id}, synchronize_session=False
    )

    db.commit()
    return anon_session.id