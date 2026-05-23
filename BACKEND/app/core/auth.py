# app/core/auth.py
import uuid
from typing import Optional

import jwt
from jwt import PyJWTError
from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models.models import User


async def verify_token_ws(websocket: WebSocket, token: Optional[str] = None) -> Optional[dict]:
    """
    Decode a Supabase JWT supplied as a WebSocket query-param.
    Returns the payload dict on success, or None if missing / invalid.
    """
    from app.core.config import settings  # local import — avoids circular dependency
    if not token:
        return None
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except PyJWTError:
        return None


def get_or_create_user(db: Session, jwt_payload: dict) -> User:
    supabase_user_id = uuid.UUID(jwt_payload["sub"])

    email = jwt_payload.get("email")

    # Supabase phone-auth puts phone at top level; email-registration puts
    # name/phone in user_metadata (options.data passed to signUp).
    user_meta = jwt_payload.get("user_metadata") or {}
    phone = jwt_payload.get("phone") or user_meta.get("phone") or None
    name  = user_meta.get("name") or jwt_payload.get("name") or None

    # Strip whitespace / empty strings to None
    if phone: phone = phone.strip() or None
    if name:  name  = name.strip()  or None

    user = db.query(User).filter(User.id == supabase_user_id).first()

    if not user:
        user = User(
            id=supabase_user_id,
            email=email,
            phone=phone,
            name=name,
            role="user",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Sync any fields that are missing or have been updated upstream
        changed = False
        if email and user.email != email:
            user.email = email
            changed = True
        # Backfill phone/name if they were blank at first signup
        if phone and not user.phone:
            user.phone = phone
            changed = True
        if name and not user.name:
            user.name = name
            changed = True
        if changed:
            db.commit()
            db.refresh(user)

    return user
