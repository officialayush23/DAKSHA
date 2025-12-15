import jwt
from cachetools import TTLCache
from fastapi import HTTPException, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from app.core.auth_optional import get_optional_user_id

from app.config import settings

# Cache tokens for 5 mins
_TOKEN_CACHE = TTLCache(maxsize=4096, ttl=300)

# HTTP Bearer – Swagger will show a simple "Authorize" with Bearer token only
security = HTTPBearer(auto_error=False)


def verify_jwt(token: str) -> Dict[str, Any]:
    if token in _TOKEN_CACHE:
        return _TOKEN_CACHE[token]
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        _TOKEN_CACHE[token] = payload
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Token: {str(e)}")


async def get_current_user_id(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Reads token from:
      - Swagger "Authorize" (HTTPBearer)
      - or plain Authorization: Bearer <token>
    """
    token = None

    if auth:
        token = auth.credentials

    if not token and authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        raise HTTPException(status_code=401, detail="Missing Authentication Token")

    payload = verify_jwt(token)
    return payload["sub"]


async def get_current_user_optional(
    user_id: str | None = Depends(get_optional_user_id),
):
    """
    Returns:
    - full user dict if logged in
    - None if guest
    """
    if not user_id:
        return None

    user = (
        supabase.table("users")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    ).data

    return user