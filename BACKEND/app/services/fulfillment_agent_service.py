# app/services/fulfillment_agent_service.py
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import Order, Shipment, Pickup, FulfillmentAttempt, AgentHandoff, User
from app.enums.db_enums import ShipmentStatusEnum, PickupStatusEnum, FulfillmentTypeEnum, ComplaintStatusEnum, EntityTypeEnum
from app.services.notification_service import notify_user

async def escalate_to_human(db: Session, order_id: uuid.UUID, reason: str, agent_run_id: uuid.UUID = None):
    order = db.get(Order, order_id)
    if not order: return {"error": "Order not found"}

    handoff = AgentHandoff(
        user_id=order.user_id,
        reason="fulfillment_failure",
        summary=reason,
        status=ComplaintStatusEnum.open
    )
    db.add(handoff)
    db.commit()

    await notify_user(
        db=db, user_id=order.user_id, 
        subject="Action Required: Support Escalation",
        message=f"I've tried reaching out regarding Order {str(order_id)[:8]}. I have escalated this to our human support team. They will contact you shortly.", 
        message_type="agent_handoff", entity_id=order.id, entity_type=EntityTypeEnum.order
    )
    return {"status": "escalated", "handoff_id": handoff.id}

async def handle_delivery_failure(db: Session, order_id: uuid.UUID, reason: str, agent_run_id: uuid.UUID = None):
    order = db.get(Order, order_id)
    shipment = db.query(Shipment).filter_by(order_id=order_id).first()
    
    if not order or not shipment: return {"error": "Order or Shipment not found"}

    shipment.status = ShipmentStatusEnum.delivery_failed

    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()
    if not attempt:
        attempt = FulfillmentAttempt(order_id=order_id, attempt_type=FulfillmentTypeEnum.delivery, status="pending", attempt_number=0)
        db.add(attempt)

    attempt.attempt_number += 1
    attempt.last_error_message = reason
    attempt.agent_run_id = agent_run_id
    attempt.next_retry_at = datetime.utcnow() + timedelta(hours=24)

    if attempt.attempt_number >= attempt.max_retries:
        attempt.status = "failed"
        db.commit()
        return await escalate_to_human(db, order_id, f"Max delivery retries ({attempt.max_retries}) reached. Reason: {reason}")

    db.commit()

    await notify_user(
        db=db, user_id=order.user_id, 
        subject="Delivery Attempt Failed 🚚",
        message=f"We tried to deliver Order {str(order_id)[:8]} but couldn't reach you. Please reply to me or use the dashboard to reschedule your delivery.", 
        message_type="fulfillment_retry", entity_id=order.id, entity_type=EntityTypeEnum.order
    )

    return {"status": "notified_user", "attempt_number": attempt.attempt_number, "attempts_left": attempt.max_retries - attempt.attempt_number}

async def reschedule_delivery(db: Session, order_id: uuid.UUID, new_address_text: str = None):
    order = db.get(Order, order_id)
    shipment = db.query(Shipment).filter_by(order_id=order_id).first()
    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()

    if new_address_text: order.delivery_address = new_address_text
    shipment.status = ShipmentStatusEnum.in_transit
    if attempt: attempt.status = "resolved"

    db.commit()

    await notify_user(
        db=db, user_id=order.user_id, 
        subject="Delivery Rescheduled ✅",
        message=f"Your order {str(order_id)[:8]} is back on track for delivery!", 
        message_type="order_update", entity_id=order.id, entity_type=EntityTypeEnum.order
    )
    return {"status": "rescheduled_successfully"}

async def handle_missed_pickup(db: Session, order_id: uuid.UUID, reason: str, agent_run_id: uuid.UUID = None):
    order = db.get(Order, order_id)
    pickup = db.query(Pickup).filter_by(order_id=order_id).first()

    pickup.status = PickupStatusEnum.missed

    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()
    if not attempt:
        attempt = FulfillmentAttempt(order_id=order_id, attempt_type=FulfillmentTypeEnum.pickup, status="pending", attempt_number=0)
        db.add(attempt)

    attempt.attempt_number += 1
    attempt.last_error_message = reason

    if attempt.attempt_number >= attempt.max_retries:
        attempt.status = "failed"
        db.commit()
        return await escalate_to_human(db, order_id, "Max pickup retries reached. User did not arrive.")

    db.commit()

    await notify_user(
        db=db, user_id=order.user_id, 
        subject="Missed Store Pickup 🏪",
        message=f"You missed your pickup slot for Order {str(order_id)[:8]}. Please reply to reschedule your pickup time.", 
        message_type="fulfillment_retry", entity_id=order.id, entity_type=EntityTypeEnum.order
    )

    return {"status": "notified_user"}

async def reschedule_pickup(db: Session, order_id: uuid.UUID, new_time: datetime):
    pickup = db.query(Pickup).filter_by(order_id=order_id).first()
    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()

    pickup.status = PickupStatusEnum.ready_for_pickup
    pickup.scheduled_time = new_time
    if attempt: attempt.status = "resolved"

    db.commit()
    order = db.get(Order, order_id)
    
    await notify_user(
        db=db, user_id=order.user_id, 
        subject="Pickup Rescheduled ✅",
        message=f"Your new pickup time is set for {new_time.strftime('%b %d, %H:%M')}.", 
        message_type="order_update", entity_id=order.id, entity_type=EntityTypeEnum.order
    )

    return {"status": "pickup_rescheduled", "new_time": str(new_time)}