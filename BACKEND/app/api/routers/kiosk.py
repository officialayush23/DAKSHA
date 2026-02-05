# app/api/routers/kiosk.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from app.schemas.schemas import KioskLoginRequest, KioskLoginResponse
from app.services.kiosk_service import login_via_kiosk
from app.core.deps import get_db, get_current_user
from app.models.models import CheckoutSession, UserSession, Kiosk,Store
from app.enums.db_enums import ChannelEnum


router = APIRouter(prefix="/kiosk", tags=["Kiosk"])


@router.get("/stores/{store_id}/kiosks")
def list_kiosks_for_store(
    store_id: UUID,
    db: Session = Depends(get_db),
):
    return (
        db.query(Kiosk)
        .filter(
            Kiosk.store_id == store_id,
            Kiosk.active.is_(True),
        )
        .all()
    )



@router.get("/stores")
def list_stores_for_kiosk(db: Session = Depends(get_db)):
    return (
        db.query(Store)
        .filter(Store.active.is_(True))
        .all()
    )


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

@router.get("/checkout/{checkout_id}")
def resume_on_kiosk(checkout_id: UUID, db: Session = Depends(get_db)):
    checkout = db.query(CheckoutSession).get(checkout_id)
    if not checkout:
        return {"error": "invalid checkout"}

    return {
        "checkout_id": checkout.id,
        "state": checkout.state,
        "locked_price": checkout.locked_price,
        "reserved_until": checkout.reserved_until,
    }

@router.get("/session/qr/{kiosk_id}")
def generate_kiosk_qr(kiosk_id: str):
    return {
        "bind_url": f"https://daksha.com/bind?session_id={uuid.uuid4()}&kiosk={kiosk_id}"
    }
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
        return {"error": "invalid session or kiosk"}

    session.user_id = user.id
    session.active_channel = ChannelEnum.kiosk
    db.commit()

    return {
        "status": "bound",
        "store_id": kiosk.store_id,
        "kiosk": kiosk.name,
    }
