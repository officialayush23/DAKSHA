# app/core/auth.py
import jwt
from typing import Optional, Dict, Any
from cachetools import TTLCache
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

# Cache tokens for 5 minutes
_TOKEN_CACHE = TTLCache(maxsize=4096, ttl=300)

# This drives Swagger’s "Authorize" dialog (single Bearer field)
security = HTTPBearer(auto_error=False)


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and validates the Supabase JWT.
    Caches decoded payload for performance.
    """
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
) -> str:
    """
    Dependency for all protected endpoints.
    Reads Authorization: Bearer <token>.
    Works with Swagger's Authorize dialog automatically.
    """
    if not auth or not auth.credentials:
        raise HTTPException(status_code=401, detail="Missing Authentication Token")

    token = auth.credentials
    payload = verify_jwt(token)
    return payload["sub"]
