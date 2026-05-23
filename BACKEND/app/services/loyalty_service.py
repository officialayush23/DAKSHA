# app/services/loyalty_service.py

import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import LoyaltyLedger, User
from app.enums.db_enums import (
    LoyaltyTransactionTypeEnum,
    EventTypeEnum,
    EntityTypeEnum,
    ChannelEnum,
)
from app.services.event_service import emit_event
from app.core.redis import redis_client

POINTS_PER_100_CURRENCY = 1

TIER_THRESHOLDS = {
    "bronze":   0,
    "silver":   100,
    "gold":     500,
    "platinum": 2000,
}

TIER_MULTIPLIERS = {
    "bronze":   1.0,
    "silver":   1.1,
    "gold":     1.25,
    "platinum": 1.5,
}

# Discount percentages for proactive wishlist offers
TIER_WISHLIST_DISCOUNT = {
    "bronze":   5,
    "silver":   8,
    "gold":     12,
    "platinum": 18,
}

POINT_EXPIRY_DAYS = 365

CACHE_TTL = 3600  # 1 hour


# -----------------------------
# Redis Keys
# -----------------------------

def _balance_key(user_id):
    return f"loyalty:balance:{user_id}"


# -----------------------------
# READ MODELS
# -----------------------------

def _redis_get(key: str):
    """Redis GET with graceful fallback — returns None if Redis is unavailable."""
    try:
        return redis_client.get(key)
    except Exception:
        return None


def _redis_setex(key: str, ttl: int, value) -> None:
    """Redis SETEX with graceful fallback — silently no-ops if Redis is unavailable."""
    try:
        redis_client.setex(key, ttl, value)
    except Exception:
        pass


def get_balance(db: Session, user_id: uuid.UUID) -> int:
    cached = _redis_get(_balance_key(user_id))
    if cached:
        return int(cached)

    balance = (
        db.query(func.coalesce(func.sum(LoyaltyLedger.points), 0))
        .filter(
            LoyaltyLedger.user_id == user_id,
            (LoyaltyLedger.expires_at.is_(None)) |
            (LoyaltyLedger.expires_at > func.now())
        )
        .scalar()
    )

    _redis_setex(_balance_key(user_id), CACHE_TTL, balance)
    return balance


def _update_cache(user_id: uuid.UUID, new_balance: int):
    _redis_setex(_balance_key(user_id), CACHE_TTL, new_balance)


def get_lifetime_earned(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.coalesce(func.sum(LoyaltyLedger.points), 0))
        .filter(
            LoyaltyLedger.user_id == user_id,
            LoyaltyLedger.transaction_type ==
            LoyaltyTransactionTypeEnum.earned_purchase,
        )
        .scalar()
    )


def compute_tier(points: int) -> str:
    """Return tier name based on lifetime earned points."""
    if points >= TIER_THRESHOLDS["platinum"]:
        return "platinum"
    if points >= TIER_THRESHOLDS["gold"]:
        return "gold"
    if points >= TIER_THRESHOLDS["silver"]:
        return "silver"
    return "bronze"


# -----------------------------
# MUTATIONS
# -----------------------------

def credit_points_for_order(
    db: Session,
    *,
    user_id: uuid.UUID,
    order_id: uuid.UUID,
    order_total: float,
    channel: ChannelEnum,
):
    user = db.get(User, user_id)
    if not user:
        return 0

    # idempotency protection
    existing = db.query(LoyaltyLedger).filter(
        LoyaltyLedger.order_id == order_id,
        LoyaltyLedger.transaction_type ==
        LoyaltyTransactionTypeEnum.earned_purchase
    ).first()

    if existing:
        return 0

    multiplier = TIER_MULTIPLIERS.get(user.loyalty_tier, 1.0)
    base_points = int(order_total // 100) * POINTS_PER_100_CURRENCY
    final_points = int(base_points * multiplier)

    if final_points <= 0:
        return 0

    current_balance = get_balance(db, user_id)
    new_balance = current_balance + final_points

    ledger = LoyaltyLedger(
        user_id=user_id,
        order_id=order_id,
        transaction_type=LoyaltyTransactionTypeEnum.earned_purchase,
        points=final_points,
        balance_snapshot=new_balance,
        expires_at=datetime.utcnow() + timedelta(days=POINT_EXPIRY_DAYS),
        reference_note=f"Earned from order ({user.loyalty_tier})",
    )

    db.add(ledger)

    # recompute tier
    lifetime = get_lifetime_earned(db, user_id) + final_points
    new_tier = compute_tier(lifetime)

    if user.loyalty_tier != new_tier:
        user.loyalty_tier = new_tier

    _update_cache(user_id, new_balance)



    return final_points


def debit_points(
    db: Session,
    *,
    user_id: uuid.UUID,
    points: int,
    reason: str,
    channel: ChannelEnum,
):
    balance = get_balance(db, user_id)

    if points > balance:
        raise ValueError("Insufficient loyalty balance")

    new_balance = balance - points

    ledger = LoyaltyLedger(
        user_id=user_id,
        transaction_type=LoyaltyTransactionTypeEnum.redeemed_checkout,
        points=-points,
        balance_snapshot=new_balance,
        reference_note=reason,
    )
    db.add(ledger)

    _update_cache(user_id, new_balance)

    

    return new_balance