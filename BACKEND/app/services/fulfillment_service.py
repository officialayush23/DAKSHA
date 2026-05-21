# app/services/fulfillment_service.py
"""
Fulfillment Service — shipment/pickup creation + order status transitions
with full omnichannel notifications (email + in-app + Telegram).
"""
import logging
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta

from app.models.models import Shipment, Pickup, Order
from app.enums.db_enums import ShipmentStatusEnum, PickupStatusEnum, OrderStatusEnum

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# STATUS → human-readable notification copy
# ─────────────────────────────────────────────────────────────────────────────
_ORDER_NOTIFICATION_COPY = {
    OrderStatusEnum.confirmed: (
        "🎉 Order Confirmed!",
        "Your DAKSHA order has been confirmed and is being prepared.",
    ),
    OrderStatusEnum.packed: (
        "📦 Order Packed",
        "Your order has been packed and is ready to hand off to the courier.",
    ),
    OrderStatusEnum.shipped: (
        "🚚 Order Shipped!",
        "Great news! Your order is on its way. You'll receive tracking updates shortly.",
    ),
    OrderStatusEnum.delivered: (
        "✅ Delivered!",
        "Your order has been delivered. We hope you love your new fashion! "
        "Rate your experience in the app.",
    ),
    OrderStatusEnum.ready_for_pickup: (
        "🏪 Ready for Pickup!",
        "Your order is ready for pickup at your selected store. Please carry a valid ID.",
    ),
    OrderStatusEnum.cancelled: (
        "❌ Order Cancelled",
        "Your order has been cancelled. Any refund will be processed within 5–7 business days.",
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# CORE: update order status + fire notifications
# ─────────────────────────────────────────────────────────────────────────────

async def update_order_status(
    db: Session,
    order_id: UUID,
    new_status: OrderStatusEnum,
    *,
    notify: bool = True,
) -> Order:
    """
    Transitions an order to new_status and sends omnichannel notifications.
    Always commits the status change even if notifications fail.
    """
    order = db.get(Order, order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")

    old_status = order.order_status
    order.order_status = new_status
    db.commit()
    db.refresh(order)

    logger.info(f"Order {order_id}: {old_status} → {new_status}")

    if notify and order.user_id:
        copy = _ORDER_NOTIFICATION_COPY.get(new_status)
        if copy:
            subject, message = copy
            try:
                from app.services.notification_service import notify_user
                from app.enums.db_enums import EntityTypeEnum
                await notify_user(
                    db=db,
                    user_id=order.user_id,
                    subject=subject,
                    message=message,
                    message_type=f"order_{new_status.value}",
                    entity_id=order_id,
                    entity_type=EntityTypeEnum.order,
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Notification failed for order {order_id} status {new_status}: {e}"
                )

    return order


# ─────────────────────────────────────────────────────────────────────────────
# SHIPMENT CREATION
# ─────────────────────────────────────────────────────────────────────────────

def create_shipment(db: Session, order_id: UUID) -> Shipment:
    shipment = Shipment(
        order_id=order_id,
        status=ShipmentStatusEnum.created,
        estimated_delivery=datetime.utcnow() + timedelta(days=3),
    )
    db.add(shipment)
    db.flush()
    return shipment


# ─────────────────────────────────────────────────────────────────────────────
# PICKUP CREATION
# ─────────────────────────────────────────────────────────────────────────────

def create_pickup(
    db: Session,
    order_id: UUID,
    store_id: UUID,
    scheduled_time: datetime | str,
) -> Pickup:
    pickup = Pickup(
        order_id=order_id,
        store_id=store_id,
        scheduled_time=scheduled_time,
        status=PickupStatusEnum.pending,
    )
    db.add(pickup)
    db.flush()
    return pickup


# ─────────────────────────────────────────────────────────────────────────────
# SHIPMENT STATUS UPDATE  (called by delivery webhook)
# ─────────────────────────────────────────────────────────────────────────────

async def update_shipment_status(
    db: Session,
    shipment_id: UUID,
    new_status: ShipmentStatusEnum,
) -> Shipment:
    """Updates shipment status and mirrors relevant transitions to the parent order."""
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise ValueError(f"Shipment {shipment_id} not found")

    shipment.status = new_status
    db.flush()

    # Mirror critical shipment statuses to the parent order
    status_mirror = {
        ShipmentStatusEnum.in_transit:       OrderStatusEnum.shipped,
        ShipmentStatusEnum.out_for_delivery: OrderStatusEnum.shipped,  # no separate out_for_delivery order status
        ShipmentStatusEnum.delivered:        OrderStatusEnum.delivered,
    }
    if new_status in status_mirror:
        await update_order_status(
            db,
            shipment.order_id,
            status_mirror[new_status],
            notify=True,
        )
    else:
        db.commit()

    return shipment
