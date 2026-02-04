# app/services/checkout_facade.py
import uuid
from sqlalchemy.orm import Session
from app.models.models import CheckoutSession, Cart
from app.enums.db_enums import CheckoutStateEnum
from app.services.checkout_orchestrator import run_checkout

def start_checkout(db: Session, user_id, session_id):
    cart = (
        db.query(Cart)
        .filter(Cart.user_id == user_id, Cart.session_id == session_id)
        .first()
    )

    if not cart:
        raise ValueError("No active cart")

    checkout = CheckoutSession(
        user_id=user_id,
        session_id=session_id,
        cart_id=cart.id,
        state=CheckoutStateEnum.INIT,
    )
    db.add(checkout)
    db.commit()
    db.refresh(checkout)

    run_checkout(db, checkout.id)

    return checkout

def get_checkout(db: Session, checkout_id: uuid.UUID):
    return db.query(CheckoutSession).get(checkout_id)
