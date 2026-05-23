# app/worker/tasks.py
import asyncio
from datetime import datetime, timedelta
from app.worker.celery_app import celery
from app.core.database import SessionLocal
from app.services.user_preference_service import build_user_preference_summary
from app.models.models import (
    CheckoutSession, UserWishlist, Order, OrderItem, OutboundMessage, User,
    ProductVariant
)
from app.enums.db_enums import (
    CheckoutStateEnum, DeliveryChannelEnum, EntityTypeEnum
)
from sqlalchemy import func
from sqlalchemy.orm import joinedload


# FIXED IMPORT: We use release_reservations for checkouts now.
from app.services.inventory_reservation_service import release_reservations


@celery.task(bind=True, max_retries=3)
def refresh_user_preferences(self, user_id: str):
    db = SessionLocal()
    try:
        build_user_preference_summary(db, user_id)
    finally:
        db.close()


@celery.task
def release_expired_reservations():
    db = SessionLocal()
    try:
        expired = db.query(CheckoutSession).filter(
            CheckoutSession.inventory_locked == True,
            CheckoutSession.reserved_until < datetime.utcnow(),
            CheckoutSession.state != CheckoutStateEnum.ORDER_CONFIRMED
        ).all()

        for checkout in expired:
            release_reservations(db, checkout.id)
            checkout.inventory_locked = False
            checkout.state = CheckoutStateEnum.CANCELLED

        db.commit()
    finally:
        db.close()


# ─── Proactive Wishlist Offer ────────────────────────────────────────────────
#
# Policy:
#   - Item must have been on the wishlist for ≥ 7 days without a purchase.
#   - No wishlist-offer notification has been sent in the last 30 days.
#   - Discount is tier-based:
#       Bronze   →  5%
#       Silver   →  8%
#       Gold     → 12%
#       Platinum → 18%
#   - We only send at most ONE offer per user per run (the oldest wishlist item).
# ─────────────────────────────────────────────────────────────────────────────

WISHLIST_AGE_DAYS        = 7
COOLDOWN_DAYS            = 30
WISHLIST_OFFER_MSG_TYPE  = "wishlist_offer"

TIER_DISCOUNT = {
    "bronze":   5,
    "silver":   8,
    "gold":     12,
    "platinum": 18,
}


@celery.task
def send_proactive_wishlist_offers():
    """
    Daily Celery beat task.
    For every user who has a wishlist item older than 7 days (without having
    purchased it in that period and without an offer notification in the last
    30 days), send a tier-based discount offer via in-app + email.
    """
    from app.services.notification_service import notify_user   # late import — async fn

    db = SessionLocal()
    try:
        cutoff_added   = datetime.utcnow() - timedelta(days=WISHLIST_AGE_DAYS)
        cutoff_cooldown = datetime.utcnow() - timedelta(days=COOLDOWN_DAYS)

        # Fetch all wishlist items older than WISHLIST_AGE_DAYS
        old_items = (
            db.query(UserWishlist)
            .options(
                joinedload(UserWishlist.variant).joinedload(ProductVariant.product),
                joinedload(UserWishlist.user),
            )
            .filter(UserWishlist.added_at <= cutoff_added)
            .all()
        )

        # Group by user — keep only the oldest item per user for a single clean offer
        user_item_map: dict = {}
        for item in old_items:
            uid = item.user_id
            if uid not in user_item_map or item.added_at < user_item_map[uid].added_at:
                user_item_map[uid] = item

        notified_count = 0

        for user_id, item in user_item_map.items():
            user: User = item.user
            if not user:
                continue

            variant: ProductVariant = item.variant
            if not variant or not variant.product:
                continue

            product_name = variant.product.name
            product_price = float(variant.base_price or 0)

            # 1. Cooldown check — did we send a wishlist offer in last 30 days?
            recent_offer = (
                db.query(OutboundMessage)
                .filter(
                    OutboundMessage.user_id == user_id,
                    OutboundMessage.message_type == WISHLIST_OFFER_MSG_TYPE,
                    OutboundMessage.channel == DeliveryChannelEnum.in_app,
                    OutboundMessage.sent_at >= cutoff_cooldown,
                )
                .first()
            )
            if recent_offer:
                continue  # still in cooldown

            # 2. Purchase check — did the user buy this variant in the last 30 days?
            purchased = (
                db.query(OrderItem)
                .join(Order, Order.id == OrderItem.order_id)
                .filter(
                    Order.user_id == user_id,
                    OrderItem.variant_id == item.product_variant_id,
                    Order.created_at >= cutoff_cooldown,
                )
                .first()
            )
            if purchased:
                continue  # already bought it recently

            # 3. Determine discount based on tier
            tier = (user.loyalty_tier or "bronze").lower()
            discount_pct = TIER_DISCOUNT.get(tier, TIER_DISCOUNT["bronze"])
            discounted_price = round(product_price * (1 - discount_pct / 100), 2)

            # 4. Build message
            subject = f"Still thinking about it? Get {discount_pct}% off — just for you 🎁"
            message = (
                f"Hi {user.name or 'there'},\n\n"
                f"You've had '{product_name}' on your wishlist for a while. "
                f"As a {tier.title()} member, we're offering you an exclusive "
                f"{discount_pct}% discount — bringing it down to ₹{discounted_price:.0f}.\n\n"
                f"This is a limited-time offer. Head to your wishlist and grab it before it's gone!"
            )

            # 5. Send via notify_user (async) — run inside event loop
            try:
                asyncio.run(notify_user(
                    db=db,
                    user_id=user_id,
                    subject=subject,
                    message=message,
                    message_type=WISHLIST_OFFER_MSG_TYPE,
                    entity_id=item.product_variant_id,
                    entity_type=EntityTypeEnum.product_variant,
                    send_email=True,
                    send_telegram=False,   # keep it to in-app + email
                    send_in_app=True,
                ))
                notified_count += 1
                print(f"[WISHLIST OFFER] Sent to user {user_id} — {discount_pct}% off {product_name}")
            except Exception as notify_err:
                print(f"[WISHLIST OFFER] Failed to notify {user_id}: {notify_err}")

        print(f"[WISHLIST OFFER] Done — {notified_count} offer(s) sent.")

    except Exception as e:
        print(f"[WISHLIST OFFER TASK ERROR]: {e}")
        raise
    finally:
        db.close()
