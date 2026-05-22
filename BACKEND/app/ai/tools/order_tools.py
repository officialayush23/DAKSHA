# app/ai/tools/order_tools.py
"""
Order tools for the Unified Agent.
Gives the agent the ability to:
  • List a user's recent orders
  • Get full details of a specific order (items, status, shipment, payment)
  • Track delivery for an order
"""
import uuid
from langchain_core.tools import tool
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.models import Order, OrderItem, OrderStatusHistory, Shipment


@tool
def get_user_orders(user_id: str, limit: int = 10) -> str:
    """
    List the user's recent orders with their status, total amount, and date.
    Always call this when the user asks about 'my orders', 'order history',
    'latest order', 'recent purchases', or similar.

    Args:
        user_id: The authenticated user's UUID.
        limit: Maximum number of orders to return (default 10).

    Returns:
        JSON string with a list of orders.
    """
    try:
        with SessionLocal() as db:
            orders = (
                db.query(Order)
                .filter(Order.user_id == uuid.UUID(user_id))
                .order_by(Order.created_at.desc())
                .limit(min(limit, 20))
                .all()
            )

            if not orders:
                return '{"orders": [], "message": "No orders found for this user."}'

            result = []
            for o in orders:
                result.append({
                    "order_id": str(o.id),
                    "status": o.order_status.value if o.order_status else "unknown",
                    "fulfillment_type": o.fulfillment_type.value if o.fulfillment_type else "unknown",
                    "total_amount": float(o.total_amount) if o.total_amount else 0.0,
                    "mutability": o.mutability_state.value if o.mutability_state else "unknown",
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                })

            import json
            return json.dumps({"orders": result, "count": len(result)})

    except Exception as e:
        return f"Error fetching orders: {str(e)}"


@tool
def get_order_details(user_id: str, order_id: str) -> str:
    """
    Get full details of a specific order — items purchased, prices, status history,
    shipment tracking info, and delivery address.
    Call this when the user asks about a specific order ID or wants to know
    what's in an order, where it is, or when it will arrive.

    Args:
        user_id: The authenticated user's UUID.
        order_id: The order UUID to look up.

    Returns:
        JSON string with full order details.
    """
    try:
        with SessionLocal() as db:
            order = (
                db.query(Order)
                .options(
                    joinedload(Order.items).joinedload(OrderItem.variant),
                    joinedload(Order.status_history),
                    joinedload(Order.shipment),
                    joinedload(Order.payment),
                )
                .filter(
                    Order.id == uuid.UUID(order_id),
                    Order.user_id == uuid.UUID(user_id),
                )
                .first()
            )

            if not order:
                return f'{{"error": "Order {order_id} not found or does not belong to this user."}}'

            # Items
            items = []
            for item in order.items:
                v = item.variant
                items.append({
                    "variant_id": str(item.product_variant_id),
                    "name": v.name if v else "Unknown",
                    "sku": v.sku if v else None,
                    "quantity": item.quantity,
                    "price_at_purchase": float(item.price_at_purchase),
                    "subtotal": float(item.price_at_purchase) * item.quantity,
                })

            # Status history (newest first)
            history = []
            for h in sorted(order.status_history, key=lambda x: x.created_at, reverse=True):
                history.append({
                    "status": h.status.value if h.status else "unknown",
                    "description": h.description if hasattr(h, "description") else None,
                    "at": h.created_at.isoformat() if h.created_at else None,
                })

            # Shipment
            shipment = None
            if order.shipment:
                s = order.shipment
                shipment = {
                    "carrier": s.carrier if hasattr(s, "carrier") else None,
                    "tracking_number": s.tracking_number if hasattr(s, "tracking_number") else None,
                    "estimated_delivery": s.estimated_delivery.isoformat() if hasattr(s, "estimated_delivery") and s.estimated_delivery else None,
                    "shipped_at": s.shipped_at.isoformat() if hasattr(s, "shipped_at") and s.shipped_at else None,
                }

            import json
            return json.dumps({
                "order_id": str(order.id),
                "status": order.order_status.value if order.order_status else "unknown",
                "fulfillment_type": order.fulfillment_type.value if order.fulfillment_type else "unknown",
                "total_amount": float(order.total_amount) if order.total_amount else 0.0,
                "delivery_address": order.delivery_address,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "items": items,
                "status_history": history,
                "shipment": shipment,
            })

    except Exception as e:
        return f"Error fetching order details: {str(e)}"
