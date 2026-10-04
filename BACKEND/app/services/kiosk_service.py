# app/services/kiosk_service.py
"""
Kiosk sign-in: phone number + one-time code.

1. login_via_kiosk(phone, kiosk)  -> a 6-digit code is sent to the customer's
   registered email / Telegram / in-app inbox; returns a challenge id.
2. verify_kiosk_otp(challenge, code) -> a short-lived DAKSHA kiosk token bound
   to this kiosk's store, plus the customer's live session.

The old flow logged anyone in with just a phone number and returned no token,
so the kiosk silently used whatever Supabase session the browser had.
Set KIOSK_OTP_REQUIRED=false only for demos.
"""
import hashlib
import json
import secrets
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import redis_client
from app.core.security import mint_kiosk_token
from app.enums.db_enums import ChannelEnum, EntityTypeEnum, EventTypeEnum
from app.models.models import Kiosk, User, UserSession
from app.services.event_service import emit_event

OTP_TTL_S = 300
MAX_ATTEMPTS = 5


def _hash(code: str, challenge: str) -> str:
    return hashlib.sha256(f"{challenge}:{code}".encode()).hexdigest()


def _normalize(phone: str) -> str:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit() or ch == "+")
    return digits


def _find_user(db: Session, phone: str) -> Optional[User]:
    p = _normalize(phone)
    candidates = {p, p.lstrip("+"), p[-10:], "+91" + p[-10:]}
    return db.query(User).filter(User.phone.in_(list(candidates))).first()


def _kiosk(db: Session, kiosk_id):
    if not kiosk_id:
        return None
    k = db.query(Kiosk).filter(Kiosk.id == kiosk_id, Kiosk.active.is_(True)).first()
    if not k:
        raise HTTPException(status_code=404, detail="Invalid kiosk")
    return k


def _finish(db: Session, user: User, kiosk) -> dict:
    session = (db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.ended_at.is_(None))
               .order_by(UserSession.started_at.desc()).first())
    if not session:
        session = UserSession(user_id=user.id, primary_channel=ChannelEnum.kiosk, active_channel=ChannelEnum.kiosk)
        db.add(session)
    else:
        session.active_channel = ChannelEnum.kiosk
    db.flush()
    emit_event(db=db, user_id=user.id, session_id=session.id, channel=ChannelEnum.kiosk,
               event_type=EventTypeEnum.session_started, entity_type=EntityTypeEnum.user_session, entity_id=session.id,
               metadata={"kiosk_id": str(kiosk.id) if kiosk else None, "store_id": str(kiosk.store_id) if kiosk else None})
    db.commit()
    token = mint_kiosk_token(user_id=user.id, kiosk_id=kiosk.id if kiosk else None,
                             store_id=kiosk.store_id if kiosk else None, phone=user.phone)
    return {"otp_required": False, "access_token": token, "expires_in": settings.KIOSK_TOKEN_TTL_MIN * 60,
            "user_id": user.id, "session_id": session.id, "kiosk_id": kiosk.id if kiosk else None,
            "store_id": kiosk.store_id if kiosk else None, "primary_channel": session.primary_channel,
            "active_channel": session.active_channel, "name": user.name, "phone": user.phone}


def login_via_kiosk(db: Session, phone: str, kiosk_id: Optional[uuid.UUID]):
    kiosk = _kiosk(db, kiosk_id)
    user = _find_user(db, phone)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this phone number. Please register via the app first.")
    if not settings.KIOSK_OTP_REQUIRED:
        return _finish(db, user, kiosk)

    challenge = secrets.token_urlsafe(16)
    code = f"{secrets.randbelow(1_000_000):06d}"
    redis_client.setex(f"kiosk:otp:{challenge}", OTP_TTL_S, json.dumps({
        "h": _hash(code, challenge), "user_id": str(user.id), "kiosk_id": str(kiosk.id) if kiosk else None, "tries": 0}))

    from app.core.background import submit
    from app.core.database import SessionLocal
    from app.services.notification_service import notify_user
    import asyncio

    def _send():
        with SessionLocal() as s:
            asyncio.run(notify_user(db=s, user_id=user.id, subject="Your DAKSHA kiosk code",
                                    message=f"Your sign-in code is {code}. It expires in 5 minutes. If this wasn't you, ignore this message.",
                                    message_type="kiosk_otp", send_email=bool(user.email), send_telegram=True, send_in_app=True))
    submit(_send)
    where = []
    if user.email:
        where.append("email " + user.email[:2] + "***" + user.email[user.email.find("@"):])
    where.append("Telegram (if linked)")
    return {"otp_required": True, "challenge_id": challenge, "sent_to": ", ".join(where), "name": user.name}


def verify_kiosk_otp(db: Session, challenge_id: str, otp: str):
    key = f"kiosk:otp:{challenge_id}"
    raw = redis_client.get(key)
    if not raw:
        raise HTTPException(status_code=410, detail="Code expired. Please start again.")
    data = json.loads(raw)
    if data["tries"] >= MAX_ATTEMPTS:
        redis_client.delete(key)
        raise HTTPException(status_code=429, detail="Too many attempts. Please start again.")
    if not secrets.compare_digest(data["h"], _hash((otp or "").strip(), challenge_id)):
        data["tries"] += 1
        redis_client.setex(key, OTP_TTL_S, json.dumps(data))
        raise HTTPException(status_code=401, detail="Incorrect code.")
    redis_client.delete(key)
    user = db.get(User, uuid.UUID(data["user_id"]))
    kiosk = _kiosk(db, uuid.UUID(data["kiosk_id"])) if data.get("kiosk_id") else None
    return _finish(db, user, kiosk)
