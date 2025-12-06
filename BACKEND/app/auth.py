import jwt
from typing import Optional, Dict, Any
from cachetools import TTLCache
from fastapi import HTTPException, Header, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

# Cache tokens for 5 mins
_TOKEN_CACHE = TTLCache(maxsize=4096, ttl=300)

# Switch to HTTPBearer. This gives the simple "Bearer Token" box in Swagger.
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
            options={"verify_exp": True}
        )
        _TOKEN_CACHE[token] = payload
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Token: {str(e)}")

async def get_current_user_id(
    # Get token from Swagger UI (HTTPBearer) or Manual Header
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    authorization: Optional[str] = Header(None)
) -> str:
    token = None

    # 1. Try Swagger UI (HTTPBearer)
    if auth:
        token = auth.credentials
    
    # 2. Try Manual Header (React/Postman)
    # Header format: "Bearer <token>"
    if not token and authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        raise HTTPException(status_code=401, detail="Missing Authentication Token")

    payload = verify_jwt(token)
    return payload["sub"]