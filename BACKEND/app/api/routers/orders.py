# app/api/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.deps import get_db, get_current_user
from app.services.order_service import list_orders, get_order

router = APIRouter(prefix="/user/orders", tags=["Orders"])

@router.get("")
def order_history(db: Session = Depends(get_db), user=Depends(get_current_user)):
    orders = list_orders(db, user.id)
    return [
        {
            "order_id": o.id,
            "status": o.order_status,
            "total": o.total_amount,
            "created_at": o.created_at,
        }
        for o in orders
    ]

@router.get("/{order_id}")
def order_detail(order_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = get_order(db, order_id, user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order.id,
        "status": order.order_status,
        "items": [
            {
                "variant_id": i.product_variant_id,
                "qty": i.quantity,
                "price": i.price_at_purchase,
            }
            for i in order.items
        ],
        "total": order.total_amount,
        "created_at": order.created_at,
    }
