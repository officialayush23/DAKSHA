# app/services/checkout_service.py
# app/services/checkout_service.py
import uuid
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.models import CheckoutSession, Cart, Order, Payment
from app.enums.db_enums import CheckoutStateEnum

RESERVATION_TTL_MINUTES = 15
MAX_PAYMENT_RETRIES = 3


ALLOWED_TRANSITIONS = {
    CheckoutStateEnum.INIT: {CheckoutStateEnum.CART_VALIDATED},
    CheckoutStateEnum.CART_VALIDATED: {CheckoutStateEnum.STOCK_RESERVED},
    CheckoutStateEnum.STOCK_RESERVED: {
        CheckoutStateEnum.PRICE_LOCKED,
        CheckoutStateEnum.ROLLED_BACK,
    },
    CheckoutStateEnum.PRICE_LOCKED: {
        CheckoutStateEnum.COUPON_APPLIED,
        CheckoutStateEnum.PAYMENT_PENDING,
    },
    CheckoutStateEnum.COUPON_APPLIED: {
        CheckoutStateEnum.PAYMENT_PENDING,
    },
    CheckoutStateEnum.PAYMENT_PENDING: {
        CheckoutStateEnum.ORDER_CONFIRMED,
        CheckoutStateEnum.PAYMENT_FAILED,
    },
    CheckoutStateEnum.PAYMENT_FAILED: {
        CheckoutStateEnum.PAYMENT_PENDING,
        CheckoutStateEnum.ROLLED_BACK,
    },
}


def transition(checkout: CheckoutSession, new_state: CheckoutStateEnum):
    if new_state not in ALLOWED_TRANSITIONS.get(checkout.state, set()):
        raise ValueError(
            f"Invalid transition {checkout.state} → {new_state}"
        )
    checkout.state = new_state


# ---------------- ENTRY POINTS ----------------

def start_checkout(db: Session, user_id: uuid.UUID, cart_id: uuid.UUID):
    session = CheckoutSession(
        user_id=user_id,
        cart_id=cart_id,
        state=CheckoutStateEnum.INIT,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def resume_checkout(db: Session, checkout_id: uuid.UUID) -> CheckoutSession:
    checkout = db.query(CheckoutSession).get(checkout_id)
    if not checkout:
        raise ValueError("Checkout not found")
    return checkout


# ---------------- PIPELINE STEPS ----------------

def validate_cart(db: Session, checkout: CheckoutSession):
    transition(checkout, CheckoutStateEnum.CART_VALIDATED)
    db.commit()


def reserve_stock(db: Session, checkout: CheckoutSession):
    checkout.reserved_until = datetime.utcnow() + timedelta(
        minutes=RESERVATION_TTL_MINUTES
    )
    transition(checkout, CheckoutStateEnum.STOCK_RESERVED)
    db.commit()


def lock_price(db: Session, checkout: CheckoutSession, total_price: float):
    checkout.locked_price = total_price
    transition(checkout, CheckoutStateEnum.PRICE_LOCKED)
    db.commit()


def apply_coupon(db: Session, checkout: CheckoutSession, discounted_price: float):
    checkout.locked_price = discounted_price
    transition(checkout, CheckoutStateEnum.COUPON_APPLIED)
    db.commit()


def initiate_payment(db: Session, checkout: CheckoutSession, method: str):
    if checkout.payment_attempts >= MAX_PAYMENT_RETRIES:
        rollback_checkout(db, checkout, "Max payment retries exceeded")
        return

    checkout.payment_attempts += 1
    transition(checkout, CheckoutStateEnum.PAYMENT_PENDING)

    payment = Payment(
        order_id=None,
        method=method,
        status="initiated",
    )
    db.add(payment)
    db.commit()


def payment_failed(db: Session, checkout: CheckoutSession, reason: str):
    checkout.last_error = reason
    transition(checkout, CheckoutStateEnum.PAYMENT_FAILED)
    db.commit()


def confirm_order(db: Session, checkout: CheckoutSession):
    order = Order(
        user_id=checkout.user_id,
        order_status="confirmed",
        total_amount=checkout.locked_price,
    )
    db.add(order)

    transition(checkout, CheckoutStateEnum.ORDER_CONFIRMED)
    db.commit()
    return order


def rollback_checkout(db: Session, checkout: CheckoutSession, reason: str):
    checkout.last_error = reason
    transition(checkout, CheckoutStateEnum.ROLLED_BACK)
    db.commit()
