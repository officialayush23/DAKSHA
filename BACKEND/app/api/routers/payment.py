# app/api/routers/payment.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.deps import get_db
from app.models.models import CheckoutSession
from app.services.checkout_service import payment_failed, confirm_order
from app.services.checkout_orchestrator import run_checkout

router = APIRouter(prefix="/payment", tags=["Payment"])

@router.post("/callback/{checkout_id}")
def payment_callback(
    checkout_id: UUID,
    payload: dict,   # gateway-specific
    db: Session = Depends(get_db)
):
    checkout = db.query(CheckoutSession).get(checkout_id)
    if not checkout:
        return {"error": "invalid checkout"}

    if payload["status"] == "success":
        confirm_order(db, checkout)
    else:
        payment_failed(db, checkout, payload.get("reason", "Payment failed"))

    # 🔁 Resume graph safely
    run_checkout(db, checkout.id)

    return {"state": checkout.state}
