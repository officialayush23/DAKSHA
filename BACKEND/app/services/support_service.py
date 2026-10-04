# app/services/support_service.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta , timezone
from typing import List, Optional, Dict, Any

from app.models.models import Return, Exchange, Complaint, Order, OrderItem, ProductVariant, OrderStatusHistory
from app.enums.db_enums import (
    ReturnStatusEnum, ExchangeStatusEnum, ComplaintStatusEnum,
    EventTypeEnum, EntityTypeEnum, OrderStatusEnum,
    OrderChangeTypeEnum, OrderChangeStatusEnum
)
from app.services.event_service import emit_event
from app.schemas.schemas import ComplaintCreate, ComplaintStatusUpdate
from app.services.notification_service import notify_user
# ==========================================
# 1. RETURN APIs
# ==========================================

def request_return(db: Session, user_id: uuid.UUID, payload):
    """
    Create a new return request
    POST /api/support/returns
    """
    # 1. Validate Order Ownership
    order = db.query(Order).filter(
        Order.id == payload.order_id,
        Order.user_id == user_id
    ).first()

    if not order:
        raise ValueError("Order not found or does not belong to user.")

    # 2. Eligibility comes from company_policy (single source of truth)
    from app.ai.policy.company_policy import RETURN_POLICY
    if order.order_status not in [OrderStatusEnum.delivered]:
        raise ValueError("Returns are only allowed for delivered orders.")
    delivered = (db.query(OrderStatusHistory)
                 .filter(OrderStatusHistory.order_id == order.id,
                         OrderStatusHistory.status == OrderStatusEnum.delivered)
                 .order_by(OrderStatusHistory.updated_at.desc()).first())
    delivered_at = delivered.updated_at if delivered else order.created_at
    if delivered_at.tzinfo is None:
        delivered_at = delivered_at.replace(tzinfo=timezone.utc)
    if delivered_at < datetime.now(timezone.utc) - timedelta(days=RETURN_POLICY.window_days):
        raise ValueError(f"The {RETURN_POLICY.window_days}-day return window for this order has closed.")
    prior = db.query(Return).filter(Return.order_id == payload.order_id,
                                    Return.status.in_([ReturnStatusEnum.requested, ReturnStatusEnum.approved])).count()
    if prior >= RETURN_POLICY.max_per_order:
        raise ValueError("A return is already open for this order (one return request per order).")

    # 3. Verify product variant belongs to order
    order_item = db.query(OrderItem).filter(
        OrderItem.order_id == payload.order_id,
        OrderItem.product_variant_id == payload.product_variant_id
    ).first()

    if not order_item:
        raise ValueError("Product variant not found in this order.")

    if payload.quantity > order_item.quantity:
        raise ValueError(f"Cannot return more than {order_item.quantity} items.")
    variant = db.get(ProductVariant, payload.product_variant_id)
    category = ((variant.product.category if variant and variant.product else "") or "").lower()
    if category in RETURN_POLICY.excluded_categories:
        raise ValueError(f"'{category}' items are non-returnable.")
    base = float(variant.base_price or 0) if variant else 0
    paid = float(order_item.price_at_purchase or 0)
    if base > 0 and (1 - paid / base) * 100 > RETURN_POLICY.excluded_if_discount_above_pct:
        raise ValueError("Items bought at more than 50% off are final sale.")

    # 4. Check if return already exists for this item
    existing_return = db.query(Return).filter(
        Return.order_id == payload.order_id,
        Return.product_variant_id == payload.product_variant_id,
        Return.status.in_([ReturnStatusEnum.requested, ReturnStatusEnum.approved])
    ).first()

    if existing_return:
        raise ValueError("A return request already exists for this item.")

    # 5. Create Return Record
    ret = Return(
        order_id=payload.order_id,
        product_variant_id=payload.product_variant_id,
        quantity=payload.quantity,
        reason=payload.reason,
        status=ReturnStatusEnum.requested,
        # 👇 FIXED: Using timezone-aware datetime for the database insert
        created_at=datetime.now(timezone.utc) 
    )
    db.add(ret)
    db.flush()

    # 6. Emit Event
    emit_event(
        db,
        user_id=user_id,
        event_type=EventTypeEnum.order_placed,  # use closest available event
        entity_type=EntityTypeEnum.order,
        entity_id=payload.order_id,
        metadata={
            "return_id": str(ret.id),
            "reason": payload.reason,
            "quantity": payload.quantity
        }
    )
    db.commit()

    # 7. Refresh to get all fields
    db.refresh(ret)
    return ret

def get_user_returns(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """
    Get all returns for a specific user — joins via Order to filter by user
    """
    returns = db.query(Return).join(
        Order, Return.order_id == Order.id
    ).filter(
        Order.user_id == user_id
    ).order_by(
        desc(Return.created_at)
    ).offset(skip).limit(limit).all()

    return returns


def get_all_returns(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ReturnStatusEnum] = None
):
    """
    Get all returns (admin only)
    """
    query = db.query(Return)

    if status:
        query = query.filter(Return.status == status)

    returns = query.order_by(desc(Return.created_at)).offset(skip).limit(limit).all()
    return returns


def get_return_by_id(db: Session, return_id: uuid.UUID, user_id: Optional[uuid.UUID] = None):
    """
    Get a specific return by ID
    """
    query = db.query(Return).filter(Return.id == return_id)

    if user_id:
        # Join to verify ownership via Order
        query = query.join(Order, Return.order_id == Order.id).filter(Order.user_id == user_id)

    ret = query.first()

    if not ret:
        raise ValueError("Return not found.")

    return ret

async def update_return_status(
    db: Session, return_id: uuid.UUID, status: ReturnStatusEnum,
    admin_id: Optional[uuid.UUID] = None, reason: Optional[str] = None
):
    ret = db.query(Return).filter(Return.id == return_id).first()
    if not ret: raise ValueError("Return not found.")

    old_status = ret.status
    ret.status = status
    db.add(ret)
    db.flush()

    order = db.query(Order).filter(Order.id == ret.order_id).first()

    emit_event(db, user_id=order.user_id if order else None, event_type=EventTypeEnum.order_placed, entity_type=EntityTypeEnum.order, entity_id=ret.order_id, metadata={"return_id": str(ret.id), "old_status": old_status.value, "new_status": status.value, "updated_by": str(admin_id) if admin_id else "system", "reason": reason})
    db.commit()
    db.refresh(ret)

    # 👇 Notification Trigger
    if order:
        await notify_user(
            db, order.user_id, f"Return Status Update: {status.value.title()}",
            f"Your return request for Order {str(order.id)[:8]} is now {status.value.replace('_', ' ')}. {reason or ''}",
            "return_update", order.id, EntityTypeEnum.order
        )

    return ret

async def cancel_return(db: Session, return_id: uuid.UUID, user_id: uuid.UUID, reason: Optional[str] = None):
    """
    Cancel a return request (user can cancel if status is 'requested')
    """
    ret = db.query(Return).join(Order, Return.order_id == Order.id).filter(Return.id == return_id, Order.user_id == user_id).first()
    if not ret: raise ValueError("Return not found or does not belong to user.")
    if ret.status != ReturnStatusEnum.requested: raise ValueError(f"Cannot cancel return with status: {ret.status.value}")

    old_status = ret.status
    ret.status = ReturnStatusEnum.cancelled
    db.commit()
    db.refresh(ret)

    await notify_user(db, user_id, "Return Cancelled", f"You have successfully cancelled the return request for Order {str(ret.order_id)[:8]}.", "return_update", ret.order_id, EntityTypeEnum.order)
    return ret


# ==========================================
# 2. CANCELLATION APIs (Order Cancellation)
# ==========================================

def request_order_cancellation(db: Session, user_id: uuid.UUID, order_id: uuid.UUID, reason: Optional[str] = None):
    """
    Request to cancel an entire order
    """
    # 1. Validate Order Ownership
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()

    if not order:
        raise ValueError("Order not found or does not belong to user.")

    # 2. Cancellation rules come from company_policy
    from app.ai.policy.company_policy import validate_cancellation
    status_value = getattr(order.order_status, "value", order.order_status)
    can_cancel, fee, policy_msg = validate_cancellation(status_value)
    if not can_cancel:
        raise ValueError(policy_msg)

    # 3. Check if cancellation already requested
    from app.models.models import OrderChangeRequest

    existing_request = db.query(OrderChangeRequest).filter(
        OrderChangeRequest.order_id == order_id,
        # FIX: correct enum value is cancel_order, not cancellation
        OrderChangeRequest.change_type == OrderChangeTypeEnum.cancel_order,
        OrderChangeRequest.status == OrderChangeStatusEnum.requested
    ).first()

    if existing_request:
        raise ValueError("Cancellation request already exists for this order.")

    # 4. Create order change request for cancellation
    change_payload = {
        "reason": reason,
        "requested_at": datetime.utcnow().isoformat(),
        "cancellation_fee": fee,
        "policy_note": policy_msg,
    }

    change_request = OrderChangeRequest(
        order_id=order_id,
        requested_by=user_id,
        # FIX: correct enum value
        change_type=OrderChangeTypeEnum.cancel_order,
        change_payload=change_payload,
        status=OrderChangeStatusEnum.requested,
        created_at=datetime.utcnow()
    )

    db.add(change_request)
    db.flush()

    emit_event(
        db,
        user_id=user_id,
        event_type=EventTypeEnum.checkout_cancelled,  # closest available
        entity_type=EntityTypeEnum.order,
        entity_id=order_id,
        metadata={
            "change_request_id": str(change_request.id),
            "reason": reason
        }
    )

    db.commit()
    db.refresh(change_request)
    return change_request


def get_cancellation_requests(
    db: Session,
    user_id: Optional[uuid.UUID] = None,
    status: Optional[OrderChangeStatusEnum] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get cancellation requests (admin: all, user: only their own)
    """
    from app.models.models import OrderChangeRequest

    # FIX: correct enum value is cancel_order, not cancellation
    query = db.query(OrderChangeRequest).filter(
        OrderChangeRequest.change_type == OrderChangeTypeEnum.cancel_order
    )

    if user_id:
        query = query.filter(OrderChangeRequest.requested_by == user_id)

    if status:
        query = query.filter(OrderChangeRequest.status == status)

    requests = query.order_by(desc(OrderChangeRequest.created_at)).offset(skip).limit(limit).all()
    return requests


async def update_cancellation_status(
    db: Session, request_id: uuid.UUID, status: OrderChangeStatusEnum,
    admin_id: uuid.UUID, decision_reason: Optional[str] = None
):
    from app.models.models import OrderChangeRequest, Order, OrderStatusHistory
    request = db.query(OrderChangeRequest).filter(OrderChangeRequest.id == request_id, OrderChangeRequest.change_type == OrderChangeTypeEnum.cancel_order).first()
    if not request: raise ValueError("Cancellation request not found.")

    old_status = request.status
    request.status = status
    request.decided_by = str(admin_id)
    request.decision_reason = decision_reason
    db.add(request)
    
    if status == OrderChangeStatusEnum.approved:
        order = db.query(Order).filter(Order.id == request.order_id).first()
        if order:
            order.order_status = OrderStatusEnum.cancelled
            db.add(OrderStatusHistory(order_id=order.id, status=OrderStatusEnum.cancelled, description=decision_reason))
    
    db.commit()
    db.refresh(request)

    await notify_user(db, request.requested_by, f"Order Cancellation {status.value.title()}", f"Your cancellation request for Order {str(request.order_id)[:8]} has been {status.value}. {decision_reason or ''}", "cancellation_update", request.order_id, EntityTypeEnum.order)
    return request


# ==========================================
# 3. COMPLAINTS APIs
# ==========================================

def file_complaint(db: Session, user_id: uuid.UUID, payload: ComplaintCreate):
    """
    File a new complaint
    """
    if payload.order_id:
        order = db.query(Order).filter(
            Order.id == payload.order_id,
            Order.user_id == user_id
        ).first()

        if not order:
            raise ValueError("Order not found or does not belong to user.")

    comp = Complaint(
        user_id=user_id,
        order_id=payload.order_id,
        session_id=payload.session_id,
        category=payload.category,
        description=payload.description,
        status=ComplaintStatusEnum.open,
        created_at=datetime.utcnow()
    )
    db.add(comp)
    db.flush()

    emit_event(
        db,
        user_id=user_id,
        event_type=EventTypeEnum.session_started,  # closest available
        entity_type=EntityTypeEnum.user_session,
        entity_id=user_id,
        metadata={
            "complaint_id": str(comp.id),
            "category": payload.category,
            "order_id": str(payload.order_id) if payload.order_id else None
        }
    )
    db.commit()
    db.refresh(comp)
    return comp


def get_user_complaints(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ComplaintStatusEnum] = None
):
    query = db.query(Complaint).filter(Complaint.user_id == user_id)

    if status:
        query = query.filter(Complaint.status == status)

    complaints = query.order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()
    return complaints


def get_all_complaints(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ComplaintStatusEnum] = None,
    category: Optional[str] = None
):
    query = db.query(Complaint)

    if status:
        query = query.filter(Complaint.status == status)

    if category:
        query = query.filter(Complaint.category == category)

    complaints = query.order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()
    return complaints


def get_complaint_by_id(db: Session, complaint_id: uuid.UUID, user_id: Optional[uuid.UUID] = None):
    query = db.query(Complaint).filter(Complaint.id == complaint_id)

    if user_id:
        query = query.filter(Complaint.user_id == user_id)

    complaint = query.first()

    if not complaint:
        raise ValueError("Complaint not found.")

    return complaint


async def update_complaint_status(
    db: Session, complaint_id: uuid.UUID, payload: ComplaintStatusUpdate,
    resolver_id: uuid.UUID, resolver_type: str = "admin"
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint: raise ValueError("Complaint not found.")

    complaint.status = payload.status
    complaint.resolution_notes = payload.resolution_notes
    complaint.resolved_by_type = resolver_type
    complaint.resolved_by_id = resolver_id
    db.commit()
    db.refresh(complaint)

    await notify_user(db, complaint.user_id, f"Complaint Status: {payload.status.value.replace('_', ' ').title()}", f"Your complaint regarding Order {str(complaint.order_id)[:8] if complaint.order_id else 'General'} has been marked as {payload.status.value.replace('_', ' ')}.", "complaint_update")
    return complaint

async def add_complaint_response(
    db: Session, complaint_id: uuid.UUID, responder_id: uuid.UUID,
    responder_type: str, message: str
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint: raise ValueError("Complaint not found.")

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    response_entry = f"\n[{timestamp}] [{responder_type} response]: {message}"
    complaint.resolution_notes = (complaint.resolution_notes or "") + response_entry
    db.commit()
    db.refresh(complaint)

    await notify_user(db, complaint.user_id, "New Message on Your Complaint", f"Support has replied to your complaint:\n\n{message}", "complaint_update")
    return complaint


def get_complaint_stats(db: Session):
    from sqlalchemy import func

    total = db.query(func.count(Complaint.id)).scalar()

    open_count = db.query(func.count(Complaint.id)).filter(
        Complaint.status == ComplaintStatusEnum.open
    ).scalar()

    in_progress_count = db.query(func.count(Complaint.id)).filter(
        Complaint.status == ComplaintStatusEnum.in_progress
    ).scalar()

    resolved_count = db.query(func.count(Complaint.id)).filter(
        Complaint.status == ComplaintStatusEnum.resolved
    ).scalar()

    category_stats_raw = db.query(
        Complaint.category,
        func.count(Complaint.id).label('count')
    ).group_by(Complaint.category).all()

    category_stats = [{"category": cat, "count": count} for cat, count in category_stats_raw if cat]

    return {
        "total": total or 0,
        "by_status": {
            "open": open_count or 0,
            "in_progress": in_progress_count or 0,
            "resolved": resolved_count or 0
        },
        "by_category": category_stats
    }


# ==========================================
# 4. EXCHANGE APIs
# ==========================================

def request_exchange(db: Session, user_id: uuid.UUID, payload):
    """
    Request an exchange
    """
    order = db.query(Order).filter(
        Order.id == payload.order_id,
        Order.user_id == user_id
    ).first()

    if not order:
        raise ValueError("Order not found")

    # Only delivered orders can be exchanged
    if order.order_status not in [OrderStatusEnum.delivered]:
        raise ValueError("Exchanges are only allowed for delivered orders.")

    new_variant = db.query(ProductVariant).filter(
        ProductVariant.id == payload.new_variant_id,
        ProductVariant.active == True
    ).first()

    if not new_variant:
        raise ValueError("New product variant not found or not active.")

    order_item = db.query(OrderItem).filter(
        OrderItem.order_id == payload.order_id,
        OrderItem.product_variant_id == payload.old_variant_id
    ).first()

    if not order_item:
        raise ValueError("Original product variant not found in this order.")

    existing_exchange = db.query(Exchange).filter(
        Exchange.order_id == payload.order_id,
        Exchange.old_variant_id == payload.old_variant_id,
        Exchange.status.in_([ExchangeStatusEnum.requested, ExchangeStatusEnum.approved])
    ).first()

    if existing_exchange:
        raise ValueError("An exchange request already exists for this item.")

    exc = Exchange(
        order_id=payload.order_id,
        old_variant_id=payload.old_variant_id,
        new_variant_id=payload.new_variant_id,
        status=ExchangeStatusEnum.requested,
        created_at=datetime.utcnow()
    )
    db.add(exc)
    db.flush()

    emit_event(
        db,
        user_id=user_id,
        event_type=EventTypeEnum.order_placed,
        entity_type=EntityTypeEnum.order,
        entity_id=payload.order_id,
        metadata={
            "exchange_id": str(exc.id),
            "old_variant": str(payload.old_variant_id),
            "new_variant": str(payload.new_variant_id)
        }
    )
    db.commit()
    db.refresh(exc)
    return exc


def get_user_exchanges(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    exchanges = db.query(Exchange).join(
        Order, Exchange.order_id == Order.id
    ).filter(
        Order.user_id == user_id
    ).order_by(
        desc(Exchange.created_at)
    ).offset(skip).limit(limit).all()

    return exchanges


def get_all_exchanges(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ExchangeStatusEnum] = None
):
    query = db.query(Exchange)

    if status:
        query = query.filter(Exchange.status == status)

    exchanges = query.order_by(desc(Exchange.created_at)).offset(skip).limit(limit).all()
    return exchanges


async def update_exchange_status(
    db: Session, exchange_id: uuid.UUID, status: ExchangeStatusEnum,
    admin_id: uuid.UUID, reason: Optional[str] = None
):
    exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()
    if not exchange: raise ValueError("Exchange not found.")

    exchange.status = status
    db.commit()
    db.refresh(exchange)

    order = db.query(Order).filter(Order.id == exchange.order_id).first()
    if order:
        await notify_user(db, order.user_id, f"Exchange Update: {status.value.title()}", f"Your exchange request for Order {str(order.id)[:8]} is now {status.value}. {reason or ''}", "exchange_update", order.id, EntityTypeEnum.order)

    return exchange