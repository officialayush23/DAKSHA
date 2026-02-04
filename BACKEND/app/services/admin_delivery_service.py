# app/services/admin_delivery_service.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.models.models import (
    Order,
    OrderStatusHistory,
    Shipment,
    User
)
from app.enums.db_enums import FulfillmentTypeEnum


# ============================
# 1. LIST ALL DELIVERY ORDERS
# ============================

def list_delivery_orders(db: Session, status: str | None = None):
    query = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.payment),
            joinedload(Order.pickup),
            joinedload(Order.items),
            joinedload(Order.status_history),
        )
        .filter(Order.fulfillment_type == FulfillmentTypeEnum.delivery)
        .order_by(desc(Order.created_at))
    )

    if status:
        query = query.filter(Order.order_status == status)

    orders = query.all()

    return [
        {
            "order_id": o.id,
            "user_id": o.user_id,
            "user_name": o.user.name if o.user else None,
            "total_amount": o.total_amount,
            "status": o.order_status,
            "created_at": o.created_at,
            "payment_status": o.payment.status if o.payment else None,
        }
        for o in orders
    ]


# ============================
# 2. ORDER DETAIL VIEW
# ============================

def get_delivery_order(db: Session, order_id):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.items),
            joinedload(Order.status_history),
            joinedload(Order.payment),
            joinedload(Order.pickup),
        )
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        return None

    return {
        "order_id": order.id,
        "user": {
            "id": order.user.id,
            "name": order.user.name,
            "email": order.user.email,
            "phone": order.user.phone,
        },
        "delivery_address": order.delivery_address,
        "status": order.order_status,
        "items": [
            {
                "variant_id": i.product_variant_id,
                "quantity": i.quantity,
                "price": i.price_at_purchase,
            }
            for i in order.items
        ],
        "history": [
            {
                "status": h.status,
                "description": h.description,
                "updated_at": h.updated_at,
            }
            for h in order.status_history
        ],
        "payment": {
            "method": order.payment.method,
            "status": order.payment.status,
            "failure_reason": order.payment.failure_reason,
        } if order.payment else None,
    }


# ============================
# 3. UPDATE DELIVERY STATUS
# ============================

def update_delivery_status(db: Session, order_id, new_status, description=None):
    order = db.query(Order).get(order_id)
    if not order:
        return None

    order.order_status = new_status

    history = OrderStatusHistory(
        order_id=order_id,
        status=new_status,
        description=description,
    )

    db.add(history)
    db.commit()
    return order
