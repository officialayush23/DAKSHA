# app/services/admin_user_service.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import uuid

from app.models.models import (
    OrderStatusHistory,
    User,
    UserSession,
    Cart,
    CartItem,
    Order,
    OrderItem,
    LoyaltyLedger,
    Coupon,
    CouponRedemption,
    UserPersonalizedOffer,
    AgentRun,
    DecisionRecord,
    Complaint,
    Review,
    Event,
)

# -----------------------------
# USER PROFILE
# -----------------------------

def get_user_profile(db: Session, user_id: uuid.UUID):
    return db.query(User).filter(User.id == user_id).first()

# -----------------------------
# SESSIONS
# -----------------------------

def get_user_sessions(db: Session, user_id: uuid.UUID):
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id)
        .order_by(UserSession.started_at.desc())
        .all()
    )

# -----------------------------
# CARTS
# -----------------------------

def get_user_carts(db: Session, user_id: uuid.UUID):
    return (
        db.query(Cart)
        .options(joinedload(Cart.items))
        .filter(Cart.user_id == user_id)
        .order_by(Cart.updated_at.desc())
        .all()
    )

# -----------------------------
# ORDERS
# -----------------------------

def get_user_orders(db: Session, user_id: uuid.UUID):
    return (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.payment),
            joinedload(Order.pickup),
            joinedload(Order.shipment),
        )
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

# -----------------------------
# LOYALTY
# -----------------------------

def get_user_loyalty_ledger(db: Session, user_id: uuid.UUID):
    return (
        db.query(LoyaltyLedger)
        .filter(LoyaltyLedger.user_id == user_id)
        .order_by(LoyaltyLedger.created_at.desc())
        .all()
    )

# -----------------------------
# COUPONS (GLOBAL + PERSONALIZED)
# -----------------------------

def get_user_coupon_redemptions(db: Session, user_id: uuid.UUID):
    return (
        db.query(CouponRedemption)
        .options(joinedload(CouponRedemption.coupon))
        .filter(CouponRedemption.user_id == user_id)
        .order_by(CouponRedemption.redeemed_at.desc())
        .all()
    )

def get_user_personalized_offers(db: Session, user_id: uuid.UUID):
    return (
        db.query(UserPersonalizedOffer)
        .filter(UserPersonalizedOffer.user_id == user_id)
        .order_by(UserPersonalizedOffer.created_at.desc())
        .all()
    )

# -----------------------------
# AGENT ACTIONS
# -----------------------------

def get_user_agent_runs(db: Session, user_id: uuid.UUID):
    return (
        db.query(AgentRun)
        .filter(AgentRun.user_id == user_id)
        .order_by(AgentRun.started_at.desc())
        .all()
    )

def get_user_decision_records(db: Session, user_id: uuid.UUID):
    return (
        db.query(DecisionRecord)
        .filter(DecisionRecord.user_id == user_id)
        .order_by(DecisionRecord.created_at.desc())
        .all()
    )

# -----------------------------
# COMPLAINTS
# -----------------------------

def get_user_complaints(db: Session, user_id: uuid.UUID):
    return (
        db.query(Complaint)
        .filter(Complaint.user_id == user_id)
        .order_by(Complaint.created_at.desc())
        .all()
    )

# -----------------------------
# REVIEWS
# -----------------------------

def get_user_reviews(db: Session, user_id: uuid.UUID):
    return (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .all()
    )

# -----------------------------
# SPEND SUMMARY
# -----------------------------

def get_user_spend_summary(db: Session, user_id: uuid.UUID):
    totals = (
        db.query(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), 0),
        )
        .filter(Order.user_id == user_id)
        .one()
    )

    return {
        "order_count": totals[0],
        "total_spent": float(totals[1]),
    }

# -----------------------------
# RAW EVENTS (OPTIONAL TAB)
# -----------------------------

def get_user_events(db: Session, user_id: uuid.UUID, limit: int = 200):
    return (
        db.query(Event)
        .filter(Event.user_id == user_id)
        .order_by(Event.created_at.desc())
        .limit(limit)
        .all()
    )

# admin_user_service.py

from app.models.models import Pickup

def get_user_pickups(db: Session, user_id: uuid.UUID):
    return (
        db.query(Pickup)
        .join(Order)
        .filter(Order.user_id == user_id)
        .order_by(Pickup.updated_at.desc())
        .all()
    )

def admin_update_user_complaint(
    db: Session,
    complaint_id: uuid.UUID,
    status,
    admin_id: uuid.UUID,
    reason: str,
):
    complaint = db.get(Complaint, complaint_id)

    if not complaint:
        return None

    complaint.status = status

    db.add(
        DecisionRecord(
            user_id=complaint.user_id,
            decision_type="admin_update_complaint",
            decision_output={
                "complaint_id": str(complaint_id),
                "new_status": status,
                "actor_type": "admin",
            },
            rationale=reason,
        )
    )
    db.commit()
    return complaint
def admin_update_user_order_status(
    db: Session,
    order_id: uuid.UUID,
    payload,
    admin_id: uuid.UUID,
    reason: str,
):
    order = db.get(Order, order_id)
    if not order:
        return None

    old_status = order.order_status
    order.order_status = payload.status

    # ✅ NEW: Add entry to history table so user sees the timeline update
    db.add(OrderStatusHistory(
        order_id=order_id,
        status=payload.status,
        description=f"Admin update: {reason}"
    ))

    # Log the Admin Decision
    db.add(
        DecisionRecord(
            user_id=order.user_id,
            decision_type="admin_update_order_status",
            decision_output={
                "order_id": str(order_id),
                "old_status": str(old_status),
                "new_status": str(payload.status),
                "actor_type": "admin",
            },
            rationale=reason,
        )
    )
    db.commit()
    return order

def admin_update_user_pickup(
    db: Session,
    pickup_id: uuid.UUID,
    *,
    status=None,
    scheduled_time=None,
    admin_id: uuid.UUID,
    reason: str,
):
    pickup = db.get(Pickup, pickup_id)
    if not pickup:
        return None

    if status:
        pickup.status = status
    if scheduled_time:
        pickup.scheduled_time = scheduled_time

    db.add(
        DecisionRecord(
            user_id=pickup.order.user_id,
            decision_type="admin_update_pickup",
            decision_output={
                "pickup_id": str(pickup_id),
                "status": status,
                "scheduled_time": str(scheduled_time) if scheduled_time else None,
                "actor_type": "admin",
            },
            rationale=reason,
        )
    )
    db.commit()
    return pickup


def list_users(db: Session, limit: int = 50, offset: int = 0):
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
