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

# ======================================================
# CONFIG (RULE-BASED, NOT AI)
# ======================================================

POINTS_PER_100_CURRENCY = 1

TIER_THRESHOLDS = {
    "silver": 0,
    "gold": 500,
    "platinum": 2000,
}

TIER_MULTIPLIERS = {
    "silver": 1.0,
    "gold": 1.2,
    "platinum": 1.5,
}

POINT_EXPIRY_DAYS = 365


# ======================================================
# READ MODELS
# ======================================================

def get_balance(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.coalesce(func.sum(LoyaltyLedger.points), 0))
        .filter(
            LoyaltyLedger.user_id == user_id,
            (LoyaltyLedger.expires_at.is_(None)) |
            (LoyaltyLedger.expires_at > func.now())
        )
        .scalar()
    )


def get_lifetime_earned(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.coalesce(func.sum(LoyaltyLedger.points), 0))
        .filter(
            LoyaltyLedger.user_id == user_id,
            LoyaltyLedger.transaction_type == LoyaltyTransactionTypeEnum.earned_purchase,
        )
        .scalar()
    )


def compute_tier(lifetime_points: int) -> str:
    if lifetime_points >= TIER_THRESHOLDS["platinum"]:
        return "platinum"
    if lifetime_points >= TIER_THRESHOLDS["gold"]:
        return "gold"
    return "silver"


# ======================================================
# MUTATIONS
# ======================================================

def credit_points_for_order(
    db: Session,
    *,
    user_id: uuid.UUID,
    order_id: uuid.UUID,
    order_total: float,
    channel: ChannelEnum,
):
    user = db.query(User).get(user_id)
    if not user:
        return 0

    multiplier = TIER_MULTIPLIERS.get(user.loyalty_tier, 1.0)
    base_points = int(order_total // 100) * POINTS_PER_100_CURRENCY
    final_points = int(base_points * multiplier)

    if final_points <= 0:
        return 0

    current_balance = get_balance(db, user_id)

    ledger = LoyaltyLedger(
        user_id=user_id,
        order_id=order_id,
        transaction_type=LoyaltyTransactionTypeEnum.earned_purchase,
        points=final_points,
        balance_snapshot=current_balance + final_points,
        expires_at=datetime.utcnow() + timedelta(days=POINT_EXPIRY_DAYS),
        reference_note=f"Earned from order ({user.loyalty_tier})",
    )
    db.add(ledger)

    # --- Tier recompute ---
    lifetime = get_lifetime_earned(db, user_id) + final_points
    new_tier = compute_tier(lifetime)

    if user.loyalty_tier != new_tier:
        user.loyalty_tier = new_tier

    # --- Event ---
    emit_event(
        db=db,
        event_type=EventTypeEnum.loyalty_credit,
        channel=channel,
        user_id=user_id,
        entity_type=EntityTypeEnum.order,
        entity_id=order_id,
        quantity=final_points,
        metadata={
            "tier": user.loyalty_tier,
            "multiplier": multiplier,
        },
    )

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

    ledger = LoyaltyLedger(
        user_id=user_id,
        transaction_type=LoyaltyTransactionTypeEnum.redeemed,
        points=-points,
        balance_snapshot=balance - points,
        reference_note=reason,
    )
    db.add(ledger)

    emit_event(
    db=db,
    event_type=EventTypeEnum.loyalty_redeem,
    channel=channel,
    user_id=user_id,
    entity_type=EntityTypeEnum.loyalty,
    entity_id=ledger.id,
    quantity=points,
    metadata={"reason": reason},
)


    return balance - points
