# app/api/routers/kiosk.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from app.core.deps import get_db, get_current_user
from app.models.models import CheckoutSession, UserSession
from app.enums.db_enums import ChannelEnum

router = APIRouter(prefix="/kiosk", tags=["Kiosk"])

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
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    session = db.query(UserSession).get(session_id)
    if not session:
        return {"error": "invalid session"}

    session.user_id = user.id
    session.active_channel = ChannelEnum.kiosk
    db.commit()

    return {"status": "bound"}
