import jwt
from cachetools import TTLCache
from fastapi import HTTPException, Header, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from app.config import settings

_TOKEN_CACHE = TTLCache(maxsize=4096, ttl=300)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def verify_jwt(token: str) -> dict:
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
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
) -> str:
    final_token = token
    if not final_token and authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            final_token = parts[1]

    if not final_token:
        raise HTTPException(status_code=401, detail="Missing Authentication")

    payload = verify_jwt(final_token)
    return payload["sub"]
