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
    raw_phone = jwt_payload.get("phone")
    phone = raw_phone if raw_phone else None
    name = jwt_payload.get("user_metadata", {}).get("name")

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
        # Only sync email — never overwrite phone/name set by user in-app
        if email and user.email != email:
            user.email = email
            db.commit()
            db.refresh(user)

    return user
