# app/graphs/checkout_nodes.py
from sqlalchemy.orm import Session
from app.services import checkout_service as svc
from app.models.models import CheckoutSession
from app.graphs.checkout_state import CheckoutGraphState


def _get_checkout(db: Session, state: CheckoutGraphState) -> CheckoutSession:
    return db.query(CheckoutSession).get(state["checkout_id"])


def validate_cart_node(db: Session, state: CheckoutGraphState):
    checkout = _get_checkout(db, state)
    svc.validate_cart(db, checkout)
    state["state"] = checkout.state
    return state


def reserve_stock_node(db: Session, state: CheckoutGraphState):
    checkout = _get_checkout(db, state)
    svc.reserve_stock(db, checkout)
    state["state"] = checkout.state
    return state


def lock_price_node(db: Session, state: CheckoutGraphState):
    checkout = _get_checkout(db, state)
    svc.lock_price(db, checkout, checkout.locked_price)
    state["state"] = checkout.state
    return state


def apply_coupon_node(db: Session, state: CheckoutGraphState):
    checkout = _get_checkout(db, state)
    # price already computed upstream
    svc.apply_coupon(db, checkout, checkout.locked_price)
    state["state"] = checkout.state
    return state


def initiate_payment_node(db: Session, state: CheckoutGraphState):
    checkout = _get_checkout(db, state)
    svc.initiate_payment(db, checkout, method="upi")
    state["state"] = checkout.state
    state["payment_attempts"] = checkout.payment_attempts
    return state


def confirm_order_node(db: Session, state: CheckoutGraphState):
    checkout = _get_checkout(db, state)
    svc.confirm_order(db, checkout)
    state["state"] = checkout.state
    return state


def rollback_node(db: Session, state: CheckoutGraphState):
    checkout = _get_checkout(db, state)
    svc.rollback_checkout(db, checkout, state.get("last_error"))
    state["state"] = checkout.state
    return state
