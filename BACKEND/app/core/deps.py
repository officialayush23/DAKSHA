# app/core/deps.py
# app/core/deps.py
from fastapi import Depends, HTTPException, status,Request
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials

from app.core.database import SessionLocal
from app.core.security import verify_supabase_jwt
from app.core.auth import get_or_create_user
from app.models.models import User
from app.enums.db_enums import UserRoleEnum, ChannelEnum


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_channel(request: Request) -> ChannelEnum:
    raw = (request.headers.get("X-Channel") or "web").lower()
    raw = {"pwa": "app"}.get(raw, raw)
    try:
        return ChannelEnum(raw)
    except ValueError:
        return ChannelEnum.web

def get_current_user(
    payload: dict = Depends(verify_supabase_jwt),
    db: Session = Depends(get_db),
) -> User:
    """
    Verifies Supabase JWT and syncs user to public.users
    """
    user = get_or_create_user(db, payload)
    # kiosk tokens pin channel + store; the chat API reads these
    if payload.get("aud") == "daksha-kiosk":
        user._token_channel = "kiosk"
        user._token_store_id = payload.get("store_id")
    return user


def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
