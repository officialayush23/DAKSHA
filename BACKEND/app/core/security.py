# app/core/security.py

# app/core/security.py

from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
import uuid

def create_access_token(
    *,
    user_id: uuid.UUID,
    email: str | None = None,
    expires_minutes: int = 60 * 24,  # 24 hours
) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "aud": "authenticated",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
    }

    return jwt.encode(
        payload,
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
