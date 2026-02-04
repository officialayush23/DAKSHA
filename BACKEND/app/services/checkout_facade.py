# app/services/checkout_facade.py
from sqlalchemy.orm import Session
from app.models.models import CheckoutSession, Cart
from app.enums.db_enums import CheckoutStateEnum, EventTypeEnum, EntityTypeEnum
from app.services.checkout_orchestrator import run_checkout
from app.services.event_service import emit_event


def _get_active_checkout(db: Session, user_id, session_id):
    return (
        db.query(CheckoutSession)
        .filter(
            CheckoutSession.user_id == user_id,
            CheckoutSession.session_id == session_id,
            CheckoutSession.state.notin_([
                CheckoutStateEnum.ORDER_CONFIRMED,
                CheckoutStateEnum.ROLLED_BACK,
            ]),
        )
        .order_by(CheckoutSession.created_at.desc())
        .first()
    )


def start_or_resume_checkout(db: Session, user_id, session_id):
    """
    SINGLE ENTRY POINT for checkout.
    Used by:
    - User APIs
    - Agent tools
    - Kiosk
    """

    existing = _get_active_checkout(db, user_id, session_id)
    if existing:
        return existing

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

    emit_event(
        db,
        user_id,
        session_id,
        None,
        EventTypeEnum.checkout_started,
        EntityTypeEnum.checkout,
        checkout.id,
    )

    run_checkout(db, checkout.id)
    return checkout


def get_checkout(db: Session, checkout_id):
    return db.query(CheckoutSession).get(checkout_id)
