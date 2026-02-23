# app/graphs/checkout_graphs.py
from langgraph.graph import StateGraph, END
from app.graphs.checkout_state import CheckoutGraphState
from app.graphs.checkout_nodes import *

def build_checkout_graph(db):
    graph = StateGraph(CheckoutGraphState)

    # Nodes
    graph.add_node("validate_cart", lambda s: validate_cart_node(db, s))
    graph.add_node("reserve_stock", lambda s: reserve_stock_node(db, s))
    graph.add_node("lock_price", lambda s: lock_price_node(db, s))
    graph.add_node("apply_coupon", lambda s: apply_coupon_node(db, s))
    graph.add_node("initiate_payment", lambda s: initiate_payment_node(db, s))
    graph.add_node("confirm_order", lambda s: confirm_order_node(db, s))
    graph.add_node("rollback", lambda s: rollback_node(db, s))

    # Linear happy path
    graph.set_entry_point("validate_cart")
    graph.add_edge("validate_cart", "reserve_stock")
    graph.add_edge("reserve_stock", "lock_price")
    graph.add_edge("lock_price", "apply_coupon")
    graph.add_edge("apply_coupon", "initiate_payment")

    # Payment branching
    graph.add_conditional_edges(
        "initiate_payment",
        lambda s: s["state"],
        {
            "PAYMENT_PENDING": END,               # waiting for gateway callback
            "PAYMENT_FAILED": "rollback",
            "ORDER_CONFIRMED": "confirm_order",
        },
    )

    graph.add_edge("confirm_order", END)
    graph.add_edge("rollback", END)

    return graph.compile()
