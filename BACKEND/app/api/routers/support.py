# app/api/routers/support.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user, get_current_admin
from app.models.models import Return, Complaint, Exchange, Order
from app.enums.db_enums import (
    ReturnStatusEnum, ComplaintStatusEnum, ExchangeStatusEnum,
    OrderStatusEnum, OrderChangeStatusEnum
)
from app.services import support_service
from app.schemas.schemas import ComplaintCreate, ComplaintStatusUpdate
from app.schemas.schemas import * 

router = APIRouter(prefix="/support", tags=["Support"])

# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================


# ==========================================
# RETURN ENDPOINTS
# ==========================================

@router.post("/returns", response_model=dict)
def create_return(
    request: ReturnRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new return request"""
    try:
        result = support_service.request_return(
            db=db,
            user_id=current_user.id,
            payload=request
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/returns/my-returns", response_model=dict)
def get_my_returns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get current user's returns"""
    returns = support_service.get_user_returns(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return {"success": True, "data": returns}


@router.get("/returns/{return_id}", response_model=dict)
def get_return(
    return_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get specific return by ID"""
    try:
        ret = support_service.get_return_by_id(
            db=db,
            return_id=return_id,
            user_id=current_user.id
        )
        return {"success": True, "data": ret}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/returns/{return_id}/cancel", response_model=dict)
def cancel_return(
    return_id: UUID,
    request: CancelRequest = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Cancel a return request"""
    try:
        reason = request.reason if request else None
        result = support_service.cancel_return(
            db=db,
            return_id=return_id,
            user_id=current_user.id,
            reason=reason
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# ADMIN RETURN ENDPOINTS
# ==========================================

@router.get("/admin/returns/all", response_model=dict)
def get_all_returns(
    status: Optional[ReturnStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get all returns (admin only)"""
    returns = support_service.get_all_returns(
        db=db,
        skip=skip,
        limit=limit,
        status=status
    )
    return {"success": True, "data": returns}


@router.patch("/admin/returns/{return_id}/status", response_model=dict)
def update_return_status(
    return_id: UUID,
    status: ReturnStatusEnum,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Update return status (admin only)"""
    try:
        result = support_service.update_return_status(
            db=db,
            return_id=return_id,
            status=status,
            admin_id=admin.id,
            reason=reason
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# COMPLAINT ENDPOINTS
# ==========================================

@router.post("/complaints", response_model=dict)
def create_complaint(
    request: ComplaintRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """File a new complaint"""
    try:
        complaint_data = ComplaintCreate(
            user_id=current_user.id,
            order_id=request.order_id,
            session_id=request.session_id,
            category=request.category,
            description=request.description
        )

        result = support_service.file_complaint(
            db=db,
            user_id=current_user.id,
            payload=complaint_data
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/complaints/my-complaints", response_model=dict)
def get_my_complaints(
    status: Optional[ComplaintStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get current user's complaints"""
    complaints = support_service.get_user_complaints(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status
    )
    return {"success": True, "data": complaints}


@router.get("/complaints/{complaint_id}", response_model=dict)
def get_complaint(
    complaint_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get specific complaint by ID"""
    try:
        complaint = support_service.get_complaint_by_id(
            db=db,
            complaint_id=complaint_id,
            user_id=current_user.id
        )
        return {"success": True, "data": complaint}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# ADMIN COMPLAINT ENDPOINTS
# ==========================================

@router.get("/admin/complaints/all", response_model=dict)
def get_all_complaints(
    status: Optional[ComplaintStatusEnum] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get all complaints (admin only)"""
    complaints = support_service.get_all_complaints(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        category=category
    )
    return {"success": True, "data": complaints}


@router.patch("/admin/complaints/{complaint_id}", response_model=dict)
def update_complaint(
    complaint_id: UUID,
    request: ComplaintUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Update complaint status (admin only)"""
    try:
        result = support_service.update_complaint_status(
            db=db,
            complaint_id=complaint_id,
            payload=request,
            resolver_id=admin.id,
            resolver_type="admin"
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/admin/complaints/{complaint_id}/respond", response_model=dict)
def respond_to_complaint(
    complaint_id: UUID,
    message: str,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Add response to complaint (admin only)"""
    try:
        result = support_service.add_complaint_response(
            db=db,
            complaint_id=complaint_id,
            responder_id=admin.id,
            responder_type="admin",
            message=message
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/admin/complaints/stats", response_model=dict)
def get_complaint_stats(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get complaint statistics (admin only)"""
    stats = support_service.get_complaint_stats(db=db)
    return {"success": True, "data": stats}


# ==========================================
# CANCELLATION ENDPOINTS
# ==========================================

@router.post("/orders/{order_id}/cancel", response_model=dict)
def request_cancellation(
    order_id: UUID,
    request: CancelRequest = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Request order cancellation"""
    try:
        reason = request.reason if request else None
        result = support_service.request_order_cancellation(
            db=db,
            user_id=current_user.id,
            order_id=order_id,
            reason=reason
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cancellations/my-requests", response_model=dict)
def get_my_cancellations(
    status: Optional[OrderChangeStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get current user's cancellation requests"""
    requests = support_service.get_cancellation_requests(
        db=db,
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    return {"success": True, "data": requests}


# ==========================================
# ADMIN CANCELLATION ENDPOINTS
# ==========================================

@router.get("/admin/cancellations/all", response_model=dict)
def get_all_cancellations(
    status: Optional[OrderChangeStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get all cancellation requests (admin only)"""
    requests = support_service.get_cancellation_requests(
        db=db,
        user_id=None,
        status=status,
        skip=skip,
        limit=limit
    )
    return {"success": True, "data": requests}


@router.patch("/admin/cancellations/{request_id}", response_model=dict)
def update_cancellation(
    request_id: UUID,
    status: OrderChangeStatusEnum,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Approve or reject cancellation (admin only)"""
    try:
        result = support_service.update_cancellation_status(
            db=db,
            request_id=request_id,
            status=status,
            admin_id=admin.id,
            decision_reason=reason
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# EXCHANGE ENDPOINTS
# ==========================================

@router.post("/exchanges", response_model=dict)
def create_exchange(
    request: ExchangeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Request an exchange"""
    try:
        result = support_service.request_exchange(
            db=db,
            user_id=current_user.id,
            payload=request
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exchanges/my-exchanges", response_model=dict)
def get_my_exchanges(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get current user's exchanges"""
    exchanges = support_service.get_user_exchanges(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return {"success": True, "data": exchanges}


# ==========================================
# ADMIN EXCHANGE ENDPOINTS
# ==========================================

@router.get("/admin/exchanges/all", response_model=dict)
def get_all_exchanges(
    status: Optional[ExchangeStatusEnum] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Get all exchanges (admin only)"""
    exchanges = support_service.get_all_exchanges(
        db=db,
        skip=skip,
        limit=limit,
        status=status
    )
    return {"success": True, "data": exchanges}


@router.patch("/admin/exchanges/{exchange_id}", response_model=dict)
def update_exchange(
    exchange_id: UUID,
    status: ExchangeStatusEnum,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Update exchange status (admin only)"""
    try:
        result = support_service.update_exchange_status(
            db=db,
            exchange_id=exchange_id,
            status=status,
            admin_id=admin.id,
            reason=reason
        )
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))