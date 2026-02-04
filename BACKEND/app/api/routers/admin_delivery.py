# app/api/routers/admin_delivery.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.services.admin_delivery_service import (
    list_delivery_orders,
    get_delivery_order,
    update_delivery_status,
)
from app.schemas.schemas import UpdateDeliveryStatusRequest

router = APIRouter(
    prefix="/admin/delivery",
    tags=["Admin – Delivery"]
)


# ============================
# LIST ALL DELIVERY ORDERS
# ============================

@router.get("/orders")
def get_delivery_orders(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return list_delivery_orders(db, status)


# ============================
# SINGLE ORDER VIEW
# ============================

@router.get("/orders/{order_id}")
def get_delivery_order_detail(
    order_id,
    db: Session = Depends(get_db),
):
    order = get_delivery_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ============================
# UPDATE STATUS
# ============================

@router.post("/orders/{order_id}/status")
def update_order_status(
    order_id,
    payload: UpdateDeliveryStatusRequest,
    db: Session = Depends(get_db),
):
    order = update_delivery_status(
        db,
        order_id,
        payload.status,
        payload.description,
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"ok": True, "new_status": payload.status}
