# app/service/checkout_service.py
# app/services/checkout_service.py
import asyncio
from datetime import datetime, timedelta, timezone # ⬅️ IMPORTED timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.notification_service import notify_user
# 👇 FIXED: Imported OrderStatusHistory
from app.models.models import (
    CheckoutSession, Order, OrderItem, CartItem, UserAddress,
    OrderStatusHistory, User, RecommendationImpression, TrainingSignal,
)
from app.enums.db_enums import (
    CheckoutStateEnum,
    OrderStatusEnum,
    ChannelEnum,
    FulfillmentTypeEnum,
    EventTypeEnum,
    EntityTypeEnum,
)

from app.services.inventory_reservation_service import (
    reserve_inventory_delivery,
    reserve_inventory_pickup,
    release_reservations,
    finalize_reservations,
)
from app.services.payment_service import process_payment
from app.services.coupon_service import finalize_coupon_redemption
from app.services.loyalty_service import credit_points_for_order, debit_points
from app.services.fulfillment_service import create_shipment, create_pickup
from app.services.email_service import send_email_and_log
from app.services.telegram_notification_service import send_telegram_and_log
from app.services.event_service import emit_event

def _aware(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _unit_price(db, variant) -> float:
    from app.services.pricing_service import resolve_variant_price
    try:
        return float(resolve_variant_price(db, variant)["final_price"])
    except Exception:
        return float(variant.base_price or 0)


def create_checkout_after_fulfillment(
    db: Session,
    *,
    user_id: UUID,
    session_id: UUID,
    cart_id: UUID,
    fulfillment_type: FulfillmentTypeEnum,
    store_id: UUID | None = None,
    channel: ChannelEnum = ChannelEnum.web,
):
    # Find any active checkout for this cart
    existing = (
        db.query(CheckoutSession)
        .filter(
            CheckoutSession.cart_id == cart_id,
            CheckoutSession.state != CheckoutStateEnum.ORDER_CONFIRMED,
        )
        .first()
    )

    from app.models.models import Cart
    cart = db.get(Cart, cart_id)
    if not cart or cart.user_id != user_id:
        raise ValueError("Cart not found for this user")

    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    if not items:
        raise ValueError("Cart is empty")

    # Lock the price the customer was shown: discount rules included, computed here, never by a client
    subtotal = round(sum(i.quantity * _unit_price(db, i.variant) for i in items), 2)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=12)

    if existing:
        # 👇 THE FIX: If it exists, we simply UPDATE it instead of creating a new row!
        if existing.fulfillment_type != fulfillment_type or str(existing.store_id) != str(store_id):
            if existing.inventory_locked:
                release_reservations(db, existing.id) # Release the old warehouse/store locks
            
            # Update to the new fulfillment method
            existing.fulfillment_type = fulfillment_type
            existing.store_id = store_id
        
        elif existing.inventory_locked:
            # same fulfilment: drop the old hold before re-holding the (possibly edited) cart
            release_reservations(db, existing.id)

        # Refresh the timer and price
        existing.state = CheckoutStateEnum.STOCK_RESERVED
        existing.locked_price = subtotal
        existing.reserved_until = expires_at
        existing.inventory_locked = True
        existing.last_active_channel = channel
        # the cart may have changed: any discount must be re-applied against the new price
        existing.applied_coupon_id = None
        existing.applied_personal_offer_id = None
        existing.discount_amount = 0

        checkout = existing
    else:
        # Create it for the very first time
        checkout = CheckoutSession(
            user_id=user_id,
            session_id=session_id,
            cart_id=cart_id,
            state=CheckoutStateEnum.STOCK_RESERVED,
            locked_price=subtotal,
            reserved_until=expires_at,
            inventory_locked=True,
            fulfillment_type=fulfillment_type,
            store_id=store_id,
            last_active_channel=channel,
        )
        db.add(checkout)
        
    db.flush()  

    # -------- RESERVE NEW INVENTORY (all-or-nothing) --------
    try:
        if fulfillment_type == FulfillmentTypeEnum.delivery:
            reserve_inventory_delivery(db, checkout.id, cart_id, expires_at)
        else:
            if not store_id:
                raise ValueError("Store required for pickup")
            reserve_inventory_pickup(db, checkout.id, cart_id, store_id, expires_at)
    except Exception:
        db.rollback()
        raise

    # -------- EVENTS --------
    emit_event(
        db,
        event_type=EventTypeEnum.checkout_started,
        user_id=user_id,
        session_id=session_id,
        channel=channel,
        entity_type=EntityTypeEnum.checkout,
        entity_id=checkout.id,
        metadata={
            "cart_value": float(subtotal),  
            "item_count": len(items),
            "fulfillment": fulfillment_type.value,
        },
    )

    emit_event(
        db,
        event_type=(
            EventTypeEnum.delivery_selected
            if fulfillment_type == FulfillmentTypeEnum.delivery
            else EventTypeEnum.pickup_selected
        ),
        user_id=user_id,
        session_id=session_id,
        channel=channel,
        entity_type=EntityTypeEnum.checkout,
        entity_id=checkout.id,
    )

    db.commit()
    db.refresh(checkout)
    return checkout

async def finalize_checkout(
    db: Session,
    *,
    checkout_id: UUID,
    delivery_address_id: UUID | None = None,  
    scheduled_time=None,
    redeem_loyalty_points: int = 0,
    agent_run_id: UUID | None = None,
    user_id: UUID | None = None,
):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout or (user_id is not None and checkout.user_id != user_id):
        raise ValueError("Checkout not found")
    if checkout.state == CheckoutStateEnum.ROLLED_BACK:
        raise ValueError("This checkout was cancelled or expired. Please start checkout again.")
    if checkout.reserved_until and _aware(checkout.reserved_until) < datetime.now(timezone.utc) and checkout.state != CheckoutStateEnum.ORDER_CONFIRMED:
        release_reservations(db, checkout.id)
        checkout.inventory_locked = False
        checkout.state = CheckoutStateEnum.ROLLED_BACK
        db.commit()
        raise ValueError("Your stock hold expired. Please start checkout again.")

    if checkout.state == CheckoutStateEnum.ORDER_CONFIRMED:
        return {"status": "already_completed"}

    user = db.get(User, checkout.user_id)
    if not user or not user.email:
        raise ValueError("An email address is required to place an order. Please update your profile.")

    # 1. Address Validation & Snapshotting ---------------------------
    address_snapshot = None
    if checkout.fulfillment_type == FulfillmentTypeEnum.delivery:
        if not delivery_address_id:
            raise ValueError("Delivery address is required for delivery orders.")
        
        addr_obj = db.query(UserAddress).filter(
            UserAddress.id == delivery_address_id, 
            UserAddress.user_id == checkout.user_id
        ).first()
        
        if not addr_obj:
            raise ValueError("Invalid delivery address.")
            
        address_snapshot = f"{addr_obj.label or 'Home'}: {addr_obj.address_line1}, {addr_obj.address_line2 or ''}, {addr_obj.city}, {addr_obj.state}, {addr_obj.pincode}"
    else:
        # 🛡️ PICKUP SAFETY: Ensure we don't save an address, but require a store/time
        delivery_address_id = None
        if not checkout.store_id:
            raise ValueError("Store ID is missing for pickup order.")
        if not scheduled_time:
            raise ValueError("Scheduled time is required for pickup orders.")
    # ----------------------------------------------------------------

    checkout.payment_attempts += 1
    final_amount = float(checkout.locked_price) - float(checkout.discount_amount or 0)

    # Loyalty redemption is validated here, against the server-side amount
    points_value = 0.0
    if redeem_loyalty_points and redeem_loyalty_points > 0:
        from app.ai.policy.company_policy import validate_loyalty_redemption, LOYALTY_POLICY
        from app.services.loyalty_service import get_balance
        if redeem_loyalty_points > get_balance(db, checkout.user_id):
            raise ValueError("You don't have that many loyalty points.")
        ok, why = validate_loyalty_redemption(redeem_loyalty_points, final_amount)
        if not ok:
            raise ValueError(why)
        points_value = (redeem_loyalty_points / 100) * LOYALTY_POLICY.rupees_per_100_points
        final_amount = max(final_amount - points_value, 0.0)
    final_amount = round(final_amount, 2)

    # -------- PROCESS PAYMENT --------
    success, payment = process_payment(
        db,
        checkout_id=checkout.id,
        amount=final_amount,
        method="card",
        agent_run_id=agent_run_id,
    )

    if not success:
        checkout.state = CheckoutStateEnum.PAYMENT_FAILED
        checkout.last_error = payment.failure_reason

        if checkout.payment_attempts >= 5:
            release_reservations(db, checkout.id)
            checkout.inventory_locked = False
            checkout.state = CheckoutStateEnum.ROLLED_BACK

        emit_event(db, event_type=EventTypeEnum.payment_failed, user_id=checkout.user_id, session_id=checkout.session_id, channel=checkout.last_active_channel, entity_type=EntityTypeEnum.checkout, entity_id=checkout.id, metadata={"reason_code": "gateway_fail", "reason": str(payment.failure_reason)})
        db.commit()
        return {"status": "payment_failed", "reason": payment.failure_reason}

    emit_event(db, event_type=EventTypeEnum.payment_success, user_id=checkout.user_id, session_id=checkout.session_id, channel=checkout.last_active_channel, entity_type=EntityTypeEnum.checkout, entity_id=checkout.id, price=final_amount)

    # -------- CREATE ORDER --------
    order = Order(
        user_id=checkout.user_id,
        fulfillment_type=checkout.fulfillment_type,
        store_id=checkout.store_id,
        delivery_address_id=delivery_address_id,  
        delivery_address=address_snapshot,        
        order_status=OrderStatusEnum.confirmed, 
        total_amount=final_amount,
        last_agent_run_id=agent_run_id,
    )
    db.add(order)
    db.flush()

    payment.order_id = order.id
    db.add(OrderStatusHistory(order_id=order.id, status=OrderStatusEnum.confirmed, description="Order placed and payment successful."))

    emit_event(db, event_type=EventTypeEnum.order_placed, user_id=checkout.user_id, session_id=checkout.session_id, channel=checkout.last_active_channel, entity_type=EntityTypeEnum.order, entity_id=order.id, price=final_amount, metadata={"checkout_duration_sec": float((datetime.now(timezone.utc) - checkout.created_at).total_seconds())})

    # -------- TRANSFER ITEMS --------
    items = db.query(CartItem).filter(CartItem.cart_id == checkout.cart_id).all()
    for item in items:
        db.add(OrderItem(order_id=order.id, product_variant_id=item.product_variant_id, quantity=item.quantity, price_at_purchase=_unit_price(db, item.variant)))
    db.query(CartItem).filter(CartItem.cart_id == checkout.cart_id).delete()

    # -------- TRAINING SIGNALS: link purchased items to recent impressions --------
    _log_purchase_training_signals(db, checkout.user_id, checkout.session_id, items, order.id)

    # -------- FINALIZE INVENTORY & COUPONS --------
    finalize_reservations(db, checkout.id)
    finalize_coupon_redemption(db, checkout.id, order.id)

    if redeem_loyalty_points > 0:
        debit_points(db=db, user_id=checkout.user_id, points=redeem_loyalty_points, reason="Checkout redemption", channel=checkout.last_active_channel)

    credit_points_for_order(db=db, user_id=checkout.user_id, order_id=order.id, order_total=final_amount, channel=checkout.last_active_channel)

    # -------- FULFILLMENT --------
    if checkout.fulfillment_type == FulfillmentTypeEnum.delivery:
        create_shipment(db, order.id)
        msg_text = f"Order `{str(order.id)[:8]}` is confirmed for Delivery.\nTotal: ₹{final_amount}"
    else:
        create_pickup(db, order.id, checkout.store_id, scheduled_time)
        msg_text = f"Order `{str(order.id)[:8]}` is confirmed for Pickup.\nScheduled for: {scheduled_time.strftime('%b %d, %H:%M')}\nTotal: ₹{final_amount}"

    checkout.state = CheckoutStateEnum.ORDER_CONFIRMED
    checkout.inventory_locked = False
    db.commit()

    # -------- OMNICHANNEL NOTIFICATION --------
    await notify_user(
        db=db,
        user_id=checkout.user_id,
        subject="Order Confirmed 🎉",
        message=msg_text,
        message_type="order_update",
        entity_id=order.id,
        entity_type=EntityTypeEnum.order
    )

    return {"status": "success", "order_id": order.id}


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING SIGNAL HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _log_purchase_training_signals(db, user_id, session_id, cart_items: list, order_id) -> None:
    """
    For each cart item, check if it had a recent recommendation impression
    (within this session or the last 24h). If so, write a 'purchase' training signal
    with reward=1.0 so the model knows what converted.
    """
    import logging as _log
    _logger = _log.getLogger(__name__)
    try:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        for item in cart_items:
            variant_id = item.product_variant_id

            impression = (
                db.query(RecommendationImpression)
                .filter(
                    RecommendationImpression.user_id == user_id,
                    RecommendationImpression.product_variant_id == variant_id,
                    RecommendationImpression.created_at >= cutoff,
                )
                .order_by(RecommendationImpression.created_at.desc())
                .first()
            )

            signal = TrainingSignal(
                user_id=user_id,
                product_variant_id=variant_id,
                signal_type="purchase",
                signal_strength=1.0,
                source="checkout",
                impression_id=impression.id if impression else None,
            )
            db.add(signal)

        db.flush()
    except Exception as e:
        _logger.warning(f"training_signals log failed: {e}")
