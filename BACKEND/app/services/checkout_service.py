# app/services/checkout_service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.models import CheckoutSession, Order, Payment
from app.enums.db_enums import CheckoutStateEnum, EventTypeEnum, EntityTypeEnum
from app.services.inventory_reservation_service import reserve_inventory, release_inventory
from app.services.payment_gateway_config_service import get_gateway_config
from app.services.event_service import emit_event

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
        raise ValueError(f"Invalid transition {checkout.state} → {new_state}")
    checkout.state = new_state

# ---------------- FSM STEPS ----------------

def validate_cart(db: Session, checkout: CheckoutSession):
    transition(checkout, CheckoutStateEnum.CART_VALIDATED)
    db.commit()

def reserve_stock(db: Session, checkout: CheckoutSession):
    if checkout.inventory_locked:
        return

    success = reserve_inventory(db, checkout.cart_id)
    if not success:
        raise ValueError("Inventory unavailable")

    checkout.inventory_locked = True
    checkout.reserved_until = datetime.utcnow() + timedelta(minutes=RESERVATION_TTL_MINUTES)
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
    cfg = get_gateway_config(db)

    if checkout.payment_attempts >= MAX_PAYMENT_RETRIES:
        rollback_checkout(db, checkout, "Max payment retries exceeded")
        return

    checkout.payment_attempts += 1
    transition(checkout, CheckoutStateEnum.PAYMENT_PENDING)

    payment = Payment(
        checkout_id=checkout.id,
        method=method,
        status="initiated",
    )
    db.add(payment)

    emit_event(
        db=db,
        user_id=checkout.user_id,
        session_id=checkout.session_id,
        event_type=EventTypeEnum.payment_started,
        entity_type=EntityTypeEnum.checkout,
        entity_id=checkout.id,
    )

    db.commit()

def payment_failed(db: Session, checkout: CheckoutSession, reason: str):
    checkout.last_error = reason
    transition(checkout, CheckoutStateEnum.PAYMENT_FAILED)

    emit_event(
        db=db,
        user_id=checkout.user_id,
        session_id=checkout.session_id,
        event_type=EventTypeEnum.payment_failed,
        entity_type=EntityTypeEnum.checkout,
        entity_id=checkout.id,
        metadata={"reason": reason},
    )

    db.commit()

def confirm_order(db: Session, checkout: CheckoutSession) -> Order:
    order = Order(
        user_id=checkout.user_id,
        order_status="confirmed",
        total_amount=checkout.locked_price,
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.flush()

    transition(checkout, CheckoutStateEnum.ORDER_CONFIRMED)

    emit_event(
        db=db,
        user_id=checkout.user_id,
        session_id=checkout.session_id,
        event_type=EventTypeEnum.order_placed,
        entity_type=EntityTypeEnum.order,
        entity_id=order.id,
        price=float(checkout.locked_price),
    )

    db.commit()
    return order

def rollback_checkout(db: Session, checkout: CheckoutSession, reason: str):
    if checkout.inventory_locked:
        release_inventory(db, checkout.cart_id)
        checkout.inventory_locked = False

    checkout.last_error = reason
    transition(checkout, CheckoutStateEnum.ROLLED_BACK)

    emit_event(
        db=db,
        user_id=checkout.user_id,
        session_id=checkout.session_id,
        event_type=EventTypeEnum.checkout_cancelled,
        entity_type=EntityTypeEnum.checkout,
        entity_id=checkout.id,
        metadata={"reason": reason},
    )

    db.commit()
