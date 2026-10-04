# app/core/security.py
"""
Bearer-token verification.

Two token types are accepted:
  1. Supabase access tokens (web/PWA/app users)            aud = "authenticated"
  2. DAKSHA kiosk tokens, minted after phone + OTP login     aud = "daksha-kiosk"
     Short-lived (KIOSK_TOKEN_TTL_MIN), bound to one kiosk/store, user role only.
"""
import time
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from app.core.config import settings

bearer_scheme = HTTPBearer(scheme_name="SupabaseJWT", description="Supabase access_token or DAKSHA kiosk token")

KIOSK_AUD = "daksha-kiosk"


def _kiosk_secret() -> str:
    return settings.KIOSK_TOKEN_SECRET or (settings.SUPABASE_JWT_SECRET + "::kiosk")


def mint_kiosk_token(*, user_id, kiosk_id=None, store_id=None, phone=None) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id), "aud": KIOSK_AUD, "iat": now, "exp": now + settings.KIOSK_TOKEN_TTL_MIN * 60,
        "jti": str(uuid.uuid4()), "channel": "kiosk", "kiosk_id": str(kiosk_id) if kiosk_id else None,
        "store_id": str(store_id) if store_id else None, "phone": phone, "role": "user",
    }
    return jwt.encode(payload, _kiosk_secret(), algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    except PyJWTError:
        pass
    try:
        return jwt.decode(token, _kiosk_secret(), algorithms=["HS256"], audience=KIOSK_AUD)
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def verify_supabase_jwt(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    return decode_token(credentials.credentials)
