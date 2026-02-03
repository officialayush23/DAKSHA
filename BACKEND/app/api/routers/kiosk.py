# app/api/routers/kiosk.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.deps import get_db
from app.models.models import CheckoutSession

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
