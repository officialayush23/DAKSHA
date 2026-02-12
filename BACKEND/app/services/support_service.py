# app/services/support_service.py
import uuid
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.models import Return, Exchange, Complaint, Order, OrderItem
from app.enums.db_enums import (
    ReturnStatusEnum, ExchangeStatusEnum, ComplaintStatusEnum, 
    EventTypeEnum, EntityTypeEnum
)
from app.services.event_service import emit_event

def request_return(db: Session, user_id: uuid.UUID, payload):
    # 1. Validate Ownership
    order = db.query(Order).filter(Order.id == payload.order_id, Order.user_id == user_id).first()
    if not order:
        raise ValueError("Order not found or does not belong to user.")

    # 2. Check Logic (e.g. Return Window)
    # if order.created_at < datetime.utcnow() - timedelta(days=30): raise ...

    # 3. Create Record
    ret = Return(
        user_id=user_id, # Ensure Model has user_id or link via Order
        order_id=payload.order_id,
        product_variant_id=payload.product_variant_id,
        quantity=payload.quantity,
        reason=payload.reason,
        status=ReturnStatusEnum.requested
    )
    db.add(ret)
    db.flush()

    # 4. Emit Event (Triggers Agent/Admin Alert)
    emit_event(
        db, 
        user_id=user_id, 
        event_type=EventTypeEnum.product_return, # Ensure Enum has this
        entity_type=EntityTypeEnum.order, 
        entity_id=payload.order_id,
        metadata={"return_id": str(ret.id), "reason": payload.reason}
    )
    db.commit()
    return ret

def request_exchange(db: Session, user_id: uuid.UUID, payload):
    order = db.query(Order).filter(Order.id == payload.order_id, Order.user_id == user_id).first()
    if not order: raise ValueError("Order not found")

    exc = Exchange(
        order_id=payload.order_id,
        old_variant_id=payload.old_variant_id,
        new_variant_id=payload.new_variant_id,
        status=ExchangeStatusEnum.requested
    )
    db.add(exc)
    db.flush()

    emit_event(
        db, 
        user_id=user_id, 
        event_type=EventTypeEnum.product_exchange, # Ensure Enum has this
        entity_type=EntityTypeEnum.order, 
        entity_id=payload.order_id,
        metadata={"exchange_id": str(exc.id)}
    )
    db.commit()
    return exc

def file_complaint(db: Session, user_id: uuid.UUID, payload):
    comp = Complaint(
        user_id=user_id,
        order_id=payload.order_id, # Optional
        category=payload.category,
        description=payload.description,
        status=ComplaintStatusEnum.open
    )
    db.add(comp)
    db.flush()

    emit_event(
        db, 
        user_id=user_id, 
        event_type=EventTypeEnum.complaint_filed, # Ensure Enum has this
        entity_type=EntityTypeEnum.user_session, 
        entity_id=user_id, # Tying to user as generic entity
        metadata={"complaint_id": str(comp.id), "category": payload.category}
    )
    db.commit()
    return comp