
# app/services/fulfillment_agent_service.py
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.models import Order, Shipment, Pickup, FulfillmentAttempt, AgentHandoff, User
from app.enums.db_enums import ShipmentStatusEnum, PickupStatusEnum, FulfillmentTypeEnum, ComplaintStatusEnum
from app.services.email_service import send_email_and_log
from app.services.telegram_notification_service import send_telegram_and_log

async def escalate_to_human(db: Session, order_id: uuid.UUID, reason: str, agent_run_id: uuid.UUID = None):
    """Tool: Hands off the issue to a human admin and notifies the user."""
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

    msg = f"⚠️ *Action Required*\nI've tried reaching out a few times regarding Order `{str(order_id)[:8]}`. I have escalated this to our human support team. They will contact you shortly."
    await send_telegram_and_log(db=db, user_id=order.user_id, text=msg, message_type="agent_handoff", entity_id=order.id)
    
    return {"status": "escalated", "handoff_id": handoff.id}

async def handle_delivery_failure(db: Session, order_id: uuid.UUID, reason: str, agent_run_id: uuid.UUID = None):
    """Tool: Logs a failed delivery, increments retry count, and proactively contacts the user to reschedule."""
    order = db.get(Order, order_id)
    shipment = db.query(Shipment).filter_by(order_id=order_id).first()
    
    if not order or not shipment:
        return {"error": "Order or Shipment not found"}

    shipment.status = ShipmentStatusEnum.delivery_failed

    # Find or create fulfillment attempt record
    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()
    if not attempt:
        attempt = FulfillmentAttempt(
            order_id=order_id, attempt_type=FulfillmentTypeEnum.delivery, status="pending", attempt_number=0
        )
        db.add(attempt)

    attempt.attempt_number += 1
    attempt.last_error_message = reason
    attempt.agent_run_id = agent_run_id
    attempt.next_retry_at = datetime.utcnow() + timedelta(hours=24) # Schedule next try

    if attempt.attempt_number >= attempt.max_retries:
        attempt.status = "failed"
        db.commit()
        return await escalate_to_human(db, order_id, f"Max delivery retries ({attempt.max_retries}) reached. Reason: {reason}")

    db.commit()

    # Notify user to reschedule
    msg = f"🚚 *Delivery Attempt Failed*\nWe tried to deliver Order `{str(order_id)[:8]}` but couldn't reach you. Please reply to me with a better time or a different address!"
    await send_telegram_and_log(db=db, user_id=order.user_id, text=msg, message_type="fulfillment_retry", entity_id=order.id)

    return {"status": "notified_user", "attempt_number": attempt.attempt_number, "attempts_left": attempt.max_retries - attempt.attempt_number}

async def reschedule_delivery(db: Session, order_id: uuid.UUID, new_address_text: str = None):
    """Tool: Fixes the failed delivery and sets it back to in_transit."""
    order = db.get(Order, order_id)
    shipment = db.query(Shipment).filter_by(order_id=order_id).first()
    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()

    if new_address_text:
        order.delivery_address = new_address_text
    
    shipment.status = ShipmentStatusEnum.in_transit
    
    if attempt:
        attempt.status = "resolved"

    db.commit()

    msg = f"✅ *Delivery Rescheduled*\nYour order `{str(order_id)[:8]}` is back on track!"
    await send_telegram_and_log(db=db, user_id=order.user_id, text=msg, message_type="order_update", entity_id=order.id)
    
    return {"status": "rescheduled_successfully"}

async def handle_missed_pickup(db: Session, order_id: uuid.UUID, reason: str, agent_run_id: uuid.UUID = None):
    """Tool: Logs a missed store pickup, increments retry count, and contacts user."""
    order = db.get(Order, order_id)
    pickup = db.query(Pickup).filter_by(order_id=order_id).first()

    pickup.status = PickupStatusEnum.missed

    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()
    if not attempt:
        attempt = FulfillmentAttempt(
            order_id=order_id, attempt_type=FulfillmentTypeEnum.pickup, status="pending", attempt_number=0
        )
        db.add(attempt)

    attempt.attempt_number += 1
    attempt.last_error_message = reason

    if attempt.attempt_number >= attempt.max_retries:
        attempt.status = "failed"
        db.commit()
        return await escalate_to_human(db, order_id, "Max pickup retries reached. User did not arrive.")

    db.commit()

    msg = f"🏪 *Missed Pickup*\nYou missed your pickup slot for Order `{str(order_id)[:8]}`. When would you like to come get it?"
    await send_telegram_and_log(db=db, user_id=order.user_id, text=msg, message_type="fulfillment_retry", entity_id=order.id)

    return {"status": "notified_user"}

async def reschedule_pickup(db: Session, order_id: uuid.UUID, new_time: datetime):
    """Tool: Updates the pickup time for a user."""
    pickup = db.query(Pickup).filter_by(order_id=order_id).first()
    attempt = db.query(FulfillmentAttempt).filter_by(order_id=order_id, status="pending").first()

    pickup.status = PickupStatusEnum.ready_for_pickup
    pickup.scheduled_time = new_time

    if attempt:
        attempt.status = "resolved"

    db.commit()
    
    order = db.get(Order, order_id)
    msg = f"✅ *Pickup Rescheduled*\nYour new pickup time is set for {new_time.strftime('%b %d, %H:%M')}."
    await send_telegram_and_log(db=db, user_id=order.user_id, text=msg, message_type="order_update", entity_id=order.id)

    return {"status": "pickup_rescheduled", "new_time": str(new_time)}