# app/services/support_service.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.models.models import Return, Exchange, Complaint, Order, OrderItem, ProductVariant
from app.enums.db_enums import (
    ReturnStatusEnum, ExchangeStatusEnum, ComplaintStatusEnum, 
    EventTypeEnum, EntityTypeEnum, OrderStatusEnum,
    OrderChangeTypeEnum, OrderChangeStatusEnum
)
from app.services.event_service import emit_event
from app.schemas.schemas import ComplaintCreate, ComplaintStatusUpdate

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
    
    # 2. Check if order is eligible for return
    # Check return window (e.g., 30 days)
    return_window_days = 30
    if order.created_at < datetime.utcnow() - timedelta(days=return_window_days):
        raise ValueError(f"Order is outside {return_window_days}-day return window.")
    
    # Check if order status allows returns
    if order.order_status not in [OrderStatusEnum.delivered, OrderStatusEnum.picked_up]:
        raise ValueError("Returns are only allowed for delivered or picked up orders.")
    
    # 3. Verify product variant belongs to order
    order_item = db.query(OrderItem).filter(
        OrderItem.order_id == payload.order_id,
        OrderItem.product_variant_id == payload.product_variant_id
    ).first()
    
    if not order_item:
        raise ValueError("Product variant not found in this order.")
    
    if payload.quantity > order_item.quantity:
        raise ValueError(f"Cannot return more than {order_item.quantity} items.")
    
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
        user_id=user_id,
        order_id=payload.order_id,
        product_variant_id=payload.product_variant_id,
        quantity=payload.quantity,
        reason=payload.reason,
        status=ReturnStatusEnum.requested,
        created_at=datetime.utcnow()
    )
    db.add(ret)
    db.flush()

    # 6. Emit Event (Triggers Agent/Admin Alert)
    emit_event(
        db, 
        user_id=user_id, 
        event_type=EventTypeEnum.product_return,
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
    Get all returns for a specific user
    GET /api/support/returns/user
    """
    returns = db.query(Return).filter(
        Return.user_id == user_id
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
    GET /api/support/returns/all
    """
    query = db.query(Return)
    
    if status:
        query = query.filter(Return.status == status)
    
    returns = query.order_by(desc(Return.created_at)).offset(skip).limit(limit).all()
    return returns


def get_return_by_id(db: Session, return_id: uuid.UUID, user_id: Optional[uuid.UUID] = None):
    """
    Get a specific return by ID
    GET /api/support/returns/{return_id}
    """
    query = db.query(Return).filter(Return.id == return_id)
    
    # If user_id provided, ensure return belongs to user
    if user_id:
        query = query.filter(Return.user_id == user_id)
    
    ret = query.first()
    
    if not ret:
        raise ValueError("Return not found.")
    
    return ret


def update_return_status(
    db: Session, 
    return_id: uuid.UUID, 
    status: ReturnStatusEnum, 
    admin_id: Optional[uuid.UUID] = None,
    reason: Optional[str] = None
):
    """
    Update return status (admin only)
    PATCH /api/support/returns/{return_id}/status
    """
    ret = db.query(Return).filter(Return.id == return_id).first()
    
    if not ret:
        raise ValueError("Return not found.")
    
    old_status = ret.status
    ret.status = status
    
    db.add(ret)
    db.flush()
    
    # Emit status change event
    emit_event(
        db,
        user_id=ret.user_id,
        event_type=EventTypeEnum.return_status_updated,
        entity_type=EntityTypeEnum.order,
        entity_id=ret.order_id,
        metadata={
            "return_id": str(ret.id),
            "old_status": old_status.value,
            "new_status": status.value,
            "updated_by": str(admin_id) if admin_id else "system",
            "reason": reason
        }
    )
    
    db.commit()
    db.refresh(ret)
    return ret


def cancel_return(db: Session, return_id: uuid.UUID, user_id: uuid.UUID, reason: Optional[str] = None):
    """
    Cancel a return request (user can cancel if status is 'requested')
    PATCH /api/support/returns/{return_id}/cancel
    """
    ret = db.query(Return).filter(
        Return.id == return_id,
        Return.user_id == user_id
    ).first()
    
    if not ret:
        raise ValueError("Return not found or does not belong to user.")
    
    # Only allow cancellation if return is in 'requested' status
    if ret.status != ReturnStatusEnum.requested:
        raise ValueError(f"Cannot cancel return with status: {ret.status.value}")
    
    old_status = ret.status
    # Update status to cancelled
    ret.status = ReturnStatusEnum.cancelled
    
    db.add(ret)
    db.flush()
    
    # Emit cancellation event
    emit_event(
        db,
        user_id=user_id,
        event_type=EventTypeEnum.return_cancelled,
        entity_type=EntityTypeEnum.order,
        entity_id=ret.order_id,
        metadata={
            "return_id": str(ret.id),
            "old_status": old_status.value,
            "new_status": ReturnStatusEnum.cancelled.value,
            "reason": reason or "User cancelled"
        }
    )
    
    db.commit()
    db.refresh(ret)
    return ret


# ==========================================
# 2. CANCELLATION APIs (Order Cancellation)
# ==========================================

def request_order_cancellation(db: Session, user_id: uuid.UUID, order_id: uuid.UUID, reason: Optional[str] = None):
    """
    Request to cancel an entire order
    POST /api/support/orders/{order_id}/cancel
    """
    # 1. Validate Order Ownership
    order = db.query(Order).filter(
        Order.id == order_id, 
        Order.user_id == user_id
    ).first()
    
    if not order:
        raise ValueError("Order not found or does not belong to user.")
    
    # 2. Check if order can be cancelled
    cancellable_statuses = [
        OrderStatusEnum.pending, 
        OrderStatusEnum.confirmed,
        OrderStatusEnum.processing
    ]
    
    if order.order_status not in cancellable_statuses:
        raise ValueError(
            f"Order cannot be cancelled in '{order.order_status.value}' status. "
            f"Only {[s.value for s in cancellable_statuses]} orders can be cancelled."
        )
    
    # 3. Check if cancellation already requested
    from app.models.models import OrderChangeRequest
    
    existing_request = db.query(OrderChangeRequest).filter(
        OrderChangeRequest.order_id == order_id,
        OrderChangeRequest.change_type == OrderChangeTypeEnum.cancellation,
        OrderChangeRequest.status == OrderChangeStatusEnum.requested
    ).first()
    
    if existing_request:
        raise ValueError("Cancellation request already exists for this order.")
    
    # 4. Create order change request for cancellation
    change_payload = {
        "reason": reason,
        "requested_at": datetime.utcnow().isoformat()
    }
    
    change_request = OrderChangeRequest(
        order_id=order_id,
        requested_by=user_id,
        change_type=OrderChangeTypeEnum.cancellation,
        change_payload=change_payload,
        status=OrderChangeStatusEnum.requested,
        created_at=datetime.utcnow()
    )
    
    db.add(change_request)
    db.flush()
    
    # 5. Emit event
    emit_event(
        db,
        user_id=user_id,
        event_type=EventTypeEnum.order_cancellation_requested,
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
    GET /api/support/cancellations
    """
    from app.models.models import OrderChangeRequest
    
    query = db.query(OrderChangeRequest).filter(
        OrderChangeRequest.change_type == OrderChangeTypeEnum.cancellation
    )
    
    if user_id:
        query = query.filter(OrderChangeRequest.requested_by == user_id)
    
    if status:
        query = query.filter(OrderChangeRequest.status == status)
    
    requests = query.order_by(desc(OrderChangeRequest.created_at)).offset(skip).limit(limit).all()
    return requests


def update_cancellation_status(
    db: Session,
    request_id: uuid.UUID,
    status: OrderChangeStatusEnum,
    admin_id: uuid.UUID,
    decision_reason: Optional[str] = None
):
    """
    Approve or reject cancellation request (admin only)
    PATCH /api/support/cancellations/{request_id}
    """
    from app.models.models import OrderChangeRequest, Order, OrderStatusHistory
    
    request = db.query(OrderChangeRequest).filter(
        OrderChangeRequest.id == request_id,
        OrderChangeRequest.change_type == OrderChangeTypeEnum.cancellation
    ).first()
    
    if not request:
        raise ValueError("Cancellation request not found.")
    
    if request.status != OrderChangeStatusEnum.requested:
        raise ValueError(f"Cannot update request with status: {request.status.value}")
    
    old_status = request.status
    # Update request
    request.status = status
    request.decided_by = str(admin_id)
    request.decision_reason = decision_reason
    
    db.add(request)
    db.flush()
    
    # If approved, update order status
    if status == OrderChangeStatusEnum.approved:
        order = db.query(Order).filter(Order.id == request.order_id).first()
        if order:
            # Save old status
            old_order_status = order.order_status
            
            # Update order status to cancelled
            order.order_status = OrderStatusEnum.cancelled
            order.mutability_state = "immutable"  # Or appropriate enum
            
            db.add(order)
            db.flush()
            
            # Add to status history
            status_history = OrderStatusHistory(
                order_id=order.id,
                status=OrderStatusEnum.cancelled,
                description=f"Order cancelled via cancellation request. Reason: {decision_reason or 'Not provided'}",
                updated_at=datetime.utcnow()
            )
            db.add(status_history)
            db.flush()
    
    # Emit event
    emit_event(
        db,
        user_id=request.requested_by,
        event_type=EventTypeEnum.cancellation_request_updated,
        entity_type=EntityTypeEnum.order,
        entity_id=request.order_id,
        metadata={
            "request_id": str(request.id),
            "old_status": old_status.value,
            "new_status": status.value,
            "reason": decision_reason,
            "decided_by": str(admin_id)
        }
    )
    
    db.commit()
    db.refresh(request)
    return request


# ==========================================
# 3. COMPLAINTS APIs
# ==========================================

def file_complaint(db: Session, user_id: uuid.UUID, payload: ComplaintCreate):
    """
    File a new complaint
    POST /api/support/complaints
    """
    # Validate order if provided
    if payload.order_id:
        order = db.query(Order).filter(
            Order.id == payload.order_id,
            Order.user_id == user_id
        ).first()
        
        if not order:
            raise ValueError("Order not found or does not belong to user.")
    
    # Create complaint
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

    # Emit event
    emit_event(
        db, 
        user_id=user_id, 
        event_type=EventTypeEnum.complaint_filed,
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
    """
    Get all complaints for a specific user
    GET /api/support/complaints/user
    """
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
    """
    Get all complaints (admin only)
    GET /api/support/complaints/all
    """
    query = db.query(Complaint)
    
    if status:
        query = query.filter(Complaint.status == status)
    
    if category:
        query = query.filter(Complaint.category == category)
    
    complaints = query.order_by(desc(Complaint.created_at)).offset(skip).limit(limit).all()
    return complaints


def get_complaint_by_id(db: Session, complaint_id: uuid.UUID, user_id: Optional[uuid.UUID] = None):
    """
    Get a specific complaint by ID
    GET /api/support/complaints/{complaint_id}
    """
    query = db.query(Complaint).filter(Complaint.id == complaint_id)
    
    if user_id:
        query = query.filter(Complaint.user_id == user_id)
    
    complaint = query.first()
    
    if not complaint:
        raise ValueError("Complaint not found.")
    
    return complaint


def update_complaint_status(
    db: Session,
    complaint_id: uuid.UUID,
    payload: ComplaintStatusUpdate,
    resolver_id: uuid.UUID,
    resolver_type: str = "admin"
):
    """
    Update complaint status and add resolution notes (admin only)
    PATCH /api/support/complaints/{complaint_id}
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    if not complaint:
        raise ValueError("Complaint not found.")
    
    # Update fields
    old_status = complaint.status
    complaint.status = payload.status
    complaint.resolution_notes = payload.resolution_notes
    complaint.resolved_by_type = resolver_type
    complaint.resolved_by_id = resolver_id
    
    db.add(complaint)
    db.flush()
    
    # Emit event
    emit_event(
        db,
        user_id=complaint.user_id,
        event_type=EventTypeEnum.complaint_updated,
        entity_type=EntityTypeEnum.user_session,
        entity_id=complaint.user_id,
        metadata={
            "complaint_id": str(complaint.id),
            "old_status": old_status.value,
            "new_status": payload.status.value,
            "resolved_by": str(resolver_id),
            "resolver_type": resolver_type
        }
    )
    
    db.commit()
    db.refresh(complaint)
    return complaint


def add_complaint_response(
    db: Session,
    complaint_id: uuid.UUID,
    responder_id: uuid.UUID,
    responder_type: str,
    message: str
):
    """
    Add a response to a complaint
    POST /api/support/complaints/{complaint_id}/respond
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    if not complaint:
        raise ValueError("Complaint not found.")
    
    # Append to resolution_notes
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    response_entry = f"\n[{timestamp}] [{responder_type} response]: {message}"
    
    if complaint.resolution_notes:
        complaint.resolution_notes += response_entry
    else:
        complaint.resolution_notes = response_entry
    
    db.add(complaint)
    db.flush()
    
    # Emit event
    emit_event(
        db,
        user_id=complaint.user_id,
        event_type=EventTypeEnum.complaint_response_added,
        entity_type=EntityTypeEnum.user_session,
        entity_id=complaint.user_id,
        metadata={
            "complaint_id": str(complaint.id),
            "responder_type": responder_type,
            "responder_id": str(responder_id)
        }
    )
    
    db.commit()
    db.refresh(complaint)
    return complaint


def get_complaint_stats(db: Session):
    """
    Get statistics about complaints (admin only)
    GET /api/support/complaints/stats
    """
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
    
    # Group by category
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
    POST /api/support/exchanges
    """
    order = db.query(Order).filter(
        Order.id == payload.order_id, 
        Order.user_id == user_id
    ).first()
    
    if not order:
        raise ValueError("Order not found")
    
    # Check if exchange is allowed based on order status
    if order.order_status not in [OrderStatusEnum.delivered, OrderStatusEnum.picked_up]:
        raise ValueError("Exchanges are only allowed for delivered or picked up orders.")
    
    # Check if new variant exists and is active
    new_variant = db.query(ProductVariant).filter(
        ProductVariant.id == payload.new_variant_id,
        ProductVariant.active == True
    ).first()
    
    if not new_variant:
        raise ValueError("New product variant not found or not active.")
    
    # Check if old variant exists in order
    order_item = db.query(OrderItem).filter(
        OrderItem.order_id == payload.order_id,
        OrderItem.product_variant_id == payload.old_variant_id
    ).first()
    
    if not order_item:
        raise ValueError("Original product variant not found in this order.")
    
    # Check if exchange already requested
    existing_exchange = db.query(Exchange).filter(
        Exchange.order_id == payload.order_id,
        Exchange.old_variant_id == payload.old_variant_id,
        Exchange.status.in_([ExchangeStatusEnum.requested, ExchangeStatusEnum.approved])
    ).first()
    
    if existing_exchange:
        raise ValueError("An exchange request already exists for this item.")
    
    # Create exchange
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
        event_type=EventTypeEnum.product_exchange,
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
    """
    Get all exchanges for a user
    GET /api/support/exchanges/user
    """
    # Join with Order to filter by user_id
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
    """
    Get all exchanges (admin only)
    GET /api/support/exchanges/all
    """
    query = db.query(Exchange)
    
    if status:
        query = query.filter(Exchange.status == status)
    
    exchanges = query.order_by(desc(Exchange.created_at)).offset(skip).limit(limit).all()
    return exchanges


def update_exchange_status(
    db: Session,
    exchange_id: uuid.UUID,
    status: ExchangeStatusEnum,
    admin_id: uuid.UUID,
    reason: Optional[str] = None
):
    """
    Update exchange status (admin only)
    PATCH /api/support/exchanges/{exchange_id}
    """
    exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()
    
    if not exchange:
        raise ValueError("Exchange not found.")
    
    old_status = exchange.status
    exchange.status = status
    
    db.add(exchange)
    db.flush()
    
    # Get order to find user_id
    order = db.query(Order).filter(Order.id == exchange.order_id).first()
    
    emit_event(
        db,
        user_id=order.user_id if order else None,
        event_type=EventTypeEnum.exchange_status_updated,
        entity_type=EntityTypeEnum.order,
        entity_id=exchange.order_id,
        metadata={
            "exchange_id": str(exchange.id),
            "old_status": old_status.value,
            "new_status": status.value,
            "reason": reason,
            "updated_by": str(admin_id)
        }
    )
    
    db.commit()
    db.refresh(exchange)
    return exchange