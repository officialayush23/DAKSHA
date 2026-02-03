# app/services/checkout_orchestrator.py
from sqlalchemy.orm import Session
from uuid import UUID
from app.graphs.checkout_graph import build_checkout_graph
from app.models.models import CheckoutSession


def run_checkout(db: Session, checkout_id: UUID):
    checkout = db.query(CheckoutSession).get(checkout_id)

    graph = build_checkout_graph(db)

    state = {
        "checkout_id": checkout.id,
        "user_id": checkout.user_id,
        "cart_id": checkout.cart_id,
        "state": checkout.state,
        "locked_price": checkout.locked_price,
        "payment_attempts": checkout.payment_attempts,
        "last_error": checkout.last_error,
    }

    return graph.invoke(state)
