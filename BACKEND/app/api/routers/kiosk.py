# app/api/routers/kiosk.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.schemas.schemas import KioskLoginRequest, KioskLoginResponse, CheckoutIntrospection
from app.services.kiosk_service import login_via_kiosk
from app.core.deps import get_db, get_current_user
from app.models.models import CheckoutSession, UserSession, Kiosk, Store
from app.enums.db_enums import ChannelEnum, CheckoutStateEnum

router = APIRouter(prefix="/kiosk", tags=["Kiosk"])


# 1. LIST ALL ACTIVE STORES
@router.get("/stores")
def list_stores_for_kiosk(db: Session = Depends(get_db)):
    return (
        db.query(Store)
        .filter(Store.active.is_(True))
        .all()
    )


# 2. LIST ALL ACTIVE KIOSKS FOR A STORE
@router.get("/stores/{store_id}/kiosks")
def list_kiosks_for_store(
    store_id: UUID,
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(
        Store.id == store_id,
        Store.active.is_(True),
    ).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found or inactive")

    return (
        db.query(Kiosk)
        .filter(
            Kiosk.store_id == store_id,
            Kiosk.active.is_(True),
        )
        .all()
    )


# 3. KIOSK LOGIN VIA PHONE
@router.post("/login", response_model=KioskLoginResponse)
def kiosk_login(
    payload: KioskLoginRequest,
    db: Session = Depends(get_db),
):
    return login_via_kiosk(
        db=db,
        phone=payload.phone,
        kiosk_id=payload.kiosk_id,
    )


# 4. RESUME INCOMPLETE CHECKOUT ON KIOSK (UPDATED)
@router.get("/checkout/{checkout_id}/resume", response_model=CheckoutIntrospection)
def resume_on_kiosk(
    checkout_id: UUID,
    db: Session = Depends(get_db),
):
    checkout = db.query(CheckoutSession).filter(
        CheckoutSession.id == checkout_id,
        CheckoutSession.state.notin_([
            CheckoutStateEnum.ORDER_CONFIRMED,
            CheckoutStateEnum.ROLLED_BACK,
        ])
    ).first()

    if not checkout:
        raise HTTPException(status_code=404, detail="No resumable checkout found")

    if checkout.reserved_until and checkout.reserved_until < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Checkout reservation expired")

    return CheckoutIntrospection(
        checkout_id=checkout.id,
        state=checkout.state,
        locked_price=float(checkout.locked_price) if checkout.locked_price else None,
        payment_attempts=checkout.payment_attempts,
        last_error=checkout.last_error,
    )


# 5. BIND SESSION TO USER VIA KIOSK - QR FLOW (UPDATED)
@router.post("/session/bind")
def bind_session_to_user(
    session_id: UUID,
    kiosk_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = db.query(UserSession).get(session_id)
    kiosk = db.query(Kiosk).get(kiosk_id)

    if not session or not kiosk:
        raise HTTPException(status_code=404, detail="Invalid session or kiosk")

    session.user_id = user.id
    session.active_channel = ChannelEnum.kiosk
    db.commit()

    return {
        "status": "bound",
        "store_id": kiosk.store_id,
        "kiosk": kiosk.name,
    }


# 6. UPDATE ACTIVE CHANNEL TO KIOSK ON EXISTING SESSION (NEW)
@router.patch("/session/{session_id}/active-channel")
def update_kiosk_active_channel(
    session_id: UUID,
    kiosk_id: UUID,
    db: Session = Depends(get_db),
):
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.ended_at.is_(None),
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    kiosk = db.query(Kiosk).filter(
        Kiosk.id == kiosk_id,
        Kiosk.active.is_(True),
    ).first()
    if not kiosk:
        raise HTTPException(status_code=404, detail="Kiosk not found or inactive")

    session.active_channel = ChannelEnum.kiosk
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "active_channel": session.active_channel,
        "store_id": kiosk.store_id,
        "kiosk_id": kiosk.id,
    }