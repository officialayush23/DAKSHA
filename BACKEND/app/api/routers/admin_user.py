# app/api/routers/admin_user.py
from app.schemas.schemas import ComplaintStatusUpdate, OrderStatusUpdate, PickupStatusUpdate
from fastapi import APIRouter, Depends, Query
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.deps import get_db, get_current_admin
from app.services.admin_user_service import *

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin – User Detail"]
)

# -----------------------------
# PROFILE
# -----------------------------
@router.get("")
def list_all_users(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    return list_users(db, limit, offset)

@router.get("/{user_id}/profile")
def profile(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_profile(db, user_id)

# -----------------------------
# SESSIONS
# -----------------------------

@router.get("/{user_id}/sessions")
def sessions(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_sessions(db, user_id)

# -----------------------------
# CARTS
# -----------------------------

@router.get("/{user_id}/carts")
def carts(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_carts(db, user_id)

# -----------------------------
# ORDERS
# -----------------------------

@router.get("/{user_id}/orders")
def orders(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_orders(db, user_id)

# -----------------------------
# LOYALTY
# -----------------------------

@router.get("/{user_id}/loyalty")
def loyalty(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_loyalty_ledger(db, user_id)

# -----------------------------
# COUPONS
# -----------------------------

@router.get("/{user_id}/coupons/redemptions")
def coupon_redemptions(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_coupon_redemptions(db, user_id)

@router.get("/{user_id}/coupons/personalized")
def personalized_coupons(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_personalized_offers(db, user_id)

# -----------------------------
# AGENT ACTIONS
# -----------------------------

@router.get("/{user_id}/agents/runs")
def agent_runs(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_agent_runs(db, user_id)

@router.get("/{user_id}/agents/decisions")
def agent_decisions(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_decision_records(db, user_id)

# -----------------------------
# COMPLAINTS
# -----------------------------

@router.get("/{user_id}/complaints")
def complaints(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_complaints(db, user_id)

# -----------------------------
# REVIEWS
# -----------------------------

@router.get("/{user_id}/reviews")
def reviews(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_reviews(db, user_id)

# -----------------------------
# SPEND SUMMARY
# -----------------------------

@router.get("/{user_id}/spend")
def spend(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_spend_summary(db, user_id)

# -----------------------------
# RAW EVENTS (DEBUG / AI AUDIT)
# -----------------------------

@router.get("/{user_id}/events")
def events(user_id: UUID, limit: int = 200, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_events(db, user_id, limit)

# admin_user.py

@router.get("/{user_id}/pickups")
def pickups(user_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return get_user_pickups(db, user_id)

@router.patch("/{user_id}/complaints/{complaint_id}")
def update_complaint_status(
    user_id: UUID,
    complaint_id: UUID,
    payload: ComplaintStatusUpdate,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return admin_update_user_complaint(
        db,
        complaint_id,
        payload.status,
        admin.id,
        reason,
    )

@router.patch("/{user_id}/orders/{order_id}/status")
def update_order_status(
    user_id: UUID,
    order_id: UUID,
    payload: OrderStatusUpdate,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    return admin_update_user_order_status(
        db,
        order_id,
        payload,
        admin.id,
        reason,
    )
@router.patch("/{user_id}/pickups/{pickup_id}")
def update_pickup(
    user_id: UUID, 
    pickup_id: UUID, 
    # Use Pydantic model for body, but extract fields manually to match service
    payload: PickupStatusUpdate, 
    reason: str = Query(...), 
    db: Session = Depends(get_db), 
    admin=Depends(get_current_admin)
):
    # ✅ NEW: Extract fields from payload to pass to service
    return admin_update_user_pickup(
        db, 
        pickup_id, 
        status=payload.status, 
        scheduled_time=payload.scheduled_time, 
        admin_id=admin.id, 
        reason=reason
    )