# app/api/routers/auth_routes.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.models.models import User
from app.enums.db_enums import ChannelEnum
from app.services import session_service

router = APIRouter(prefix="/auth", tags=["Auth & Sessions"])

class GuestInitRequest(BaseModel):
    anonymous_id: UUID
    channel: ChannelEnum = ChannelEnum.web

class MergeRequest(BaseModel):
    anonymous_id: UUID

@router.post("/guest/init")
def init_guest_session(
    payload: GuestInitRequest, 
    db: Session = Depends(get_db)
):
    """
    Called when a user lands on the site/app without logging in.
    """
    session = session_service.get_or_create_active_session(
        db, 
        anonymous_id=payload.anonymous_id, 
        channel=payload.channel
    )
    return {"session_id": session.id, "anonymous_id": session.anonymous_id}

@router.post("/sync")
def sync_user_session(
    payload: MergeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Called immediately after Supabase Login on the frontend.
    Merges the previous anonymous activity into the authenticated user.
    """
    session_service.merge_anonymous_session(db, payload.anonymous_id, user.id)
    
    # Ensure a fresh active session exists for the User ID
    active_session = session_service.get_or_create_active_session(db, user_id=user.id)
    
    return {"status": "merged", "active_session_id": active_session.id}