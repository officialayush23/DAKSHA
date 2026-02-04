# app/api/routers/checkout.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.deps import get_db, get_current_user
from app.services.checkout_facade import start_checkout, get_checkout

router = APIRouter(prefix="/checkout", tags=["Checkout"])

@router.post("/start")
def checkout_start(db: Session = Depends(get_db), user=Depends(get_current_user)):
    session = user.sessions[-1]  # active guaranteed by policy
    checkout = start_checkout(db, user.id, session.id)
    return {
        "checkout_id": checkout.id,
        "state": checkout.state,
        "reserved_until": checkout.reserved_until,
    }

@router.get("/{checkout_id}")
def checkout_status(checkout_id: UUID, db: Session = Depends(get_db)):
    checkout = get_checkout(db, checkout_id)
    return {
        "checkout_id": checkout.id,
        "state": checkout.state,
        "locked_price": checkout.locked_price,
        "reserved_until": checkout.reserved_until,
        "payment_attempts": checkout.payment_attempts,
        "last_error": checkout.last_error,
    }
