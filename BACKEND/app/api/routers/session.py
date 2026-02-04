# app/api/routers/session.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.enums.db_enums import ChannelEnum
from app.services.session_service import (
    start_session, get_active_session, switch_channel
)

router = APIRouter(prefix="/session", tags=["Session"])

@router.post("/start")
def start(channel: ChannelEnum, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = start_session(db, user.id, channel)
    return {
        "session_id": session.id,
        "primary_channel": session.primary_channel,
        "active_channel": session.active_channel,
        "started_at": session.started_at,
    }

@router.get("/active")
def active(db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = get_active_session(db, user.id)
    if not session:
        return None
    return {
        "session_id": session.id,
        "primary_channel": session.primary_channel,
        "active_channel": session.active_channel,
        "started_at": session.started_at,
    }

@router.post("/switch-channel")
def switch(channel: ChannelEnum, db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = get_active_session(db, user.id)
    switch_channel(db, session, channel)
    return {"status": "ok"}
