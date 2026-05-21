# app/api/routers/delivery_webhook.py
"""
Delivery Tracking Webhook
──────────────────────────
Receives courier status pushes and writes to delivery_tracking table.
Also exposes a /simulate endpoint for dev/QA testing without a real courier.

Real couriers POST to:  POST /delivery/webhook/{order_id}
QA simulation:          POST /delivery/webhook/simulate/{order_id}
"""
import logging
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_admin
from app.core.config import settings
from app.models.models import DeliveryTracking, Shipment, Order
from app.enums.db_enums import ShipmentStatusEnum, OrderStatusEnum
from app.services.fulfillment_service import update_shipment_status, update_order_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/delivery", tags=["Delivery Webhook"])


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class CourierPush(BaseModel):
    status: str                        # e.g. "in_transit", "out_for_delivery", "delivered"
    carrier_event_code: Optional[str] = None
    carrier_message: Optional[str]    = None
    location_text: Optional[str]      = None
    is_exception: bool                 = False
    exception_reason: Optional[str]   = None
    recorded_at: Optional[datetime]   = None


class SimulatePayload(BaseModel):
    status: str = "out_for_delivery"
    location_text: Optional[str] = "Mumbai Distribution Centre"
    carrier_message: Optional[str] = "Package scanned at hub"


# ─────────────────────────────────────────────────────────────────────────────
# STATUS STRING → ENUM MAPPING
# ─────────────────────────────────────────────────────────────────────────────

_STATUS_MAP: dict[str, ShipmentStatusEnum] = {
    "created":           ShipmentStatusEnum.created,
    "in_transit":        ShipmentStatusEnum.in_transit,
    "out_for_delivery":  ShipmentStatusEnum.out_for_delivery,
    "delivered":         ShipmentStatusEnum.delivered,
    "delayed":           ShipmentStatusEnum.delayed,
    "cancelled":         ShipmentStatusEnum.cancelled,
    "delivery_failed":   ShipmentStatusEnum.delivery_failed,
}


# ─────────────────────────────────────────────────────────────────────────────
# CORE PUSH PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────

async def _process_push(db: Session, order_id: UUID, push: CourierPush) -> dict:
    """Shared logic for both real webhook and simulate endpoint."""
    # 1. Verify order exists
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    # 2. Write delivery_tracking event
    tracking = DeliveryTracking(
        order_id=order_id,
        status=push.status,
        location_text=push.location_text,
        carrier_event_code=push.carrier_event_code,
        carrier_message=push.carrier_message,
        is_exception=push.is_exception,
        exception_reason=push.exception_reason,
        recorded_at=push.recorded_at or datetime.now(timezone.utc),
    )
    db.add(tracking)
    db.flush()

    # 3. Update shipment + order status (with notifications)
    shipment = (
        db.query(Shipment)
        .filter(Shipment.order_id == order_id)
        .order_by(Shipment.created_at.desc())
        .first()
    )

    new_shipment_status = _STATUS_MAP.get(push.status)
    if shipment and new_shipment_status:
        try:
            await update_shipment_status(db, shipment.id, new_shipment_status)
        except Exception as e:
            logger.warning(f"⚠️ update_shipment_status failed: {e}")
            db.commit()  # still commit the tracking row
    else:
        db.commit()

    logger.info(f"📦 delivery_tracking: order={order_id} status={push.status}")
    return {"status": "ok", "tracking_id": str(tracking.id), "order_id": str(order_id)}


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/webhook/{order_id}")
async def courier_webhook(
    order_id: UUID,
    push: CourierPush,
    db: Session = Depends(get_db),
    x_webhook_secret: Optional[str] = Header(None),
):
    """
    Real courier push endpoint.
    Couriers should POST with header X-Webhook-Secret matching WEBHOOK_SECRET env var.
    """
    # Basic shared-secret auth (optional — skip if not configured)
    webhook_secret = getattr(settings, "WEBHOOK_SECRET", None)
    if webhook_secret and x_webhook_secret != webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    return await _process_push(db, order_id, push)


@router.post("/webhook/simulate/{order_id}")
async def simulate_delivery_push(
    order_id: UUID,
    payload: SimulatePayload,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """
    Admin-only endpoint to simulate a courier push for QA/demo.
    Lets you progress an order through delivery states without a real courier.
    """
    push = CourierPush(
        status=payload.status,
        location_text=payload.location_text,
        carrier_message=payload.carrier_message,
        carrier_event_code="SIM_EVENT",
        is_exception=False,
        recorded_at=datetime.now(timezone.utc),
    )
    return await _process_push(db, order_id, push)


@router.get("/tracking/{order_id}")
def get_delivery_tracking(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    """Returns the full delivery timeline for an order (latest first)."""
    events = (
        db.query(DeliveryTracking)
        .filter(DeliveryTracking.order_id == order_id)
        .order_by(DeliveryTracking.recorded_at.desc())
        .all()
    )
    return [
        {
            "id":                 str(e.id),
            "status":             e.status,
            "location_text":      e.location_text,
            "carrier_event_code": e.carrier_event_code,
            "carrier_message":    e.carrier_message,
            "is_exception":       e.is_exception,
            "exception_reason":   e.exception_reason,
            "recorded_at":        e.recorded_at.isoformat() if e.recorded_at else None,
        }
        for e in events
    ]
