# app/api/routers/payment.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.deps import get_db
from app.models.models import CheckoutSession, Payment, PaymentGatewayConfig
from app.services.checkout_service import confirm_order, payment_failed
from app.services.checkout_orchestrator import run_checkout

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post("/pay/{checkout_id}")
def dummy_pay(
    checkout_id: UUID,
    idempotency_key: str = Header(...),
    db: Session = Depends(get_db),
):
    checkout = db.query(CheckoutSession).get(checkout_id)
    if not checkout:
        raise HTTPException(404, "Invalid checkout")

    existing = (
        db.query(Payment)
        .filter_by(checkout_id=checkout_id, idempotency_key=idempotency_key)
        .first()
    )
    if existing:
        return {"status": existing.status}

    cfg = db.query(PaymentGatewayConfig).get(1)
    status = cfg.force_status if cfg and cfg.force_status else "success"

    payment = Payment(
        checkout_id=checkout_id,
        method="dummy",
        status=status,
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    db.commit()

    if status == "success":
        confirm_order(db, checkout)
    else:
        payment_failed(db, checkout, "Dummy failure")

    run_checkout(db, checkout.id)
    return {"status": status}
