# app/routers/omni.py
from fastapi import APIRouter, Depends
from typing import Optional
from app.core.auth import get_current_user_id
from app.services.omni_session_service import OmniSessionService

router = APIRouter(prefix="/omni", tags=["Omnichannel Sessions"])


@router.post("/session")
async def upsert_session(
    channel_type: str,
    channel_id: str,
    chat_session_id: Optional[str] = None,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    """
    Called by web/kiosk clients to bind a device/cookie to a user + chat session.
    """
    session_id = OmniSessionService.upsert_session(
        channel_type=channel_type,
        channel_id=channel_id,
        user_id=user_id,
        chat_session_id=chat_session_id,
        active_cart_id=None,
    )
    return {"session_id": session_id}
