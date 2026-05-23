# app/services/kiosk_service.py
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.models import User, UserSession, Kiosk
from app.enums.db_enums import ChannelEnum
from app.services.event_service import emit_event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum


def login_via_kiosk(
    db: Session,
    phone: str,
    kiosk_id: Optional[uuid.UUID],
):
    # 1. Validate kiosk (only if kiosk_id supplied)
    kiosk = None
    if kiosk_id:
        kiosk = db.query(Kiosk).filter(
            Kiosk.id == kiosk_id,
            Kiosk.active.is_(True)
        ).first()
        if not kiosk:
            raise HTTPException(status_code=404, detail="Invalid kiosk")

    # 2. Find user by phone — just check existence, no OTP required
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found with this phone number. Please register via the app first."
        )

    # 3. Get active session or create one
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user.id,
            UserSession.ended_at.is_(None),
        )
        .first()
    )

    if not session:
        session = UserSession(
            user_id=user.id,
            primary_channel=ChannelEnum.web,
            active_channel=ChannelEnum.kiosk,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    else:
        session.active_channel = ChannelEnum.kiosk
        db.commit()

    # 4. Emit session event
    emit_event(
        db=db,
        user_id=user.id,
        session_id=session.id,
        channel=ChannelEnum.kiosk,
        event_type=EventTypeEnum.session_started,
        entity_type=EntityTypeEnum.user_session,
        entity_id=session.id,
        metadata={
            "kiosk_id": str(kiosk.id) if kiosk else None,
            "store_id": str(kiosk.store_id) if kiosk else None,
        },
    )

    return {
        "user_id": user.id,
        "session_id": session.id,
        "kiosk_id": kiosk.id if kiosk else None,
        "store_id": kiosk.store_id if kiosk else None,
        "primary_channel": session.primary_channel,
        "active_channel": session.active_channel,
        "name": user.name,
        "phone": user.phone,
    }
