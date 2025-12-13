# app/core/auth_optional.py

from fastapi import Header
from typing import Optional
import jwt

# If you use Supabase JWT, you may NOT need the secret here
SUPABASE_JWT_SECRET = None  # or load from env if needed


async def get_optional_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extract user_id from Authorization: Bearer <token>
    If missing or invalid → return None instead of raising.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]

    try:
        # Supabase JWT is NOT validated here — we only decode.
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub")
    except Exception:
        return None
