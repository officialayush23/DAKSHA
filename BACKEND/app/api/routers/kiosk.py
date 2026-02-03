# app/api/routers/kiosk.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from app.core.deps import get_db
from app.models.models import CheckoutSession
from app.core.deps import get_db, get_current_user
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
    """
    Frontend calls this to show a QR. 
    Encoded URL: https://daksha.com/bind?kiosk_session=UUID
    """
    # This just returns the metadata for the frontend to render the QR
    return {"bind_url": f"https://daksha.com/bind?session_id={uuid.uuid4()}&kiosk={kiosk_id}"}

@router.post("/session/bind")
def bind_session_to_user(session_id: UUID, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """
    When user scans QR and is logged in on mobile, 
    this links the Kiosk session to their permanent user record.
    """
    session = db.query(Session).get(session_id)
    if session:
        session.user_id = user.id
        db.commit()
    return {"status": "bound", "user": user.name}