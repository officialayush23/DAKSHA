# app/service/checkout_service.py
# app/services/checkout_service.py
import asyncio
from datetime import datetime, timedelta, timezone # ⬅️ IMPORTED timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.services.notification_service import notify_user
# 👇 FIXED: Imported OrderStatusHistory
from app.models.models import CheckoutSession, Order, OrderItem, CartItem, UserAddress, OrderStatusHistory,User
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
    # Prevent duplicate checkout reservations
    existing = (
        db.query(CheckoutSession)
        .filter(
            CheckoutSession.cart_id == cart_id,
            CheckoutSession.inventory_locked == True,
            CheckoutSession.state != CheckoutStateEnum.ORDER_CONFIRMED,
        )
        .first()
    )
    if existing:
        return existing

    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    if not items:
        raise ValueError("Cart is empty")

    subtotal = sum(i.quantity * i.variant.base_price for i in items)
    
    # ⬅️ FIXED: Use timezone-aware datetime
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=12)

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

    # -------- RESERVE INVENTORY --------
    if fulfillment_type == FulfillmentTypeEnum.delivery:
        reserve_inventory_delivery(db, checkout.id, cart_id, expires_at)
    else:
        if not store_id:
            raise ValueError("Store required for pickup")
        reserve_inventory_pickup(db, checkout.id, cart_id, store_id, expires_at)

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
):
    checkout = db.get(CheckoutSession, checkout_id)
    if not checkout:
        raise ValueError("Checkout not found")

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
    final_amount = float(checkout.locked_price) - float(checkout.discount_amount)

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
            checkout.state = CheckoutStateEnum.CANCELLED

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
        db.add(OrderItem(order_id=order.id, product_variant_id=item.product_variant_id, quantity=item.quantity, price_at_purchase=item.variant.base_price))
    db.query(CartItem).filter(CartItem.cart_id == checkout.cart_id).delete()

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