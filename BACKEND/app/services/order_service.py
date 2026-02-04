# app/services/order_service.py

from sqlalchemy.orm import Session
from app.models.models import Order
import uuid

def list_orders(db: Session, user_id: uuid.UUID):
    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

def get_order(db: Session, order_id: uuid.UUID, user_id: uuid.UUID):
    return (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )
