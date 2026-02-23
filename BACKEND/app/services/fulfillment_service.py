# app/services/fulfillment_service.py
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from app.models.models import Shipment, Pickup
from app.enums.db_enums import ShipmentStatusEnum, PickupStatusEnum

def create_shipment(db: Session, order_id: UUID) -> Shipment:
    shipment = Shipment(
        order_id=order_id,
        status=ShipmentStatusEnum.created,
        estimated_delivery=datetime.utcnow() + timedelta(days=3)
    )
    db.add(shipment)
    db.flush()
    return shipment

def create_pickup(db: Session, order_id: UUID, store_id: UUID, scheduled_time: datetime | str) -> Pickup:
    pickup = Pickup(
        order_id=order_id,
        store_id=store_id,
        scheduled_time=scheduled_time,
        status=PickupStatusEnum.pending,
    )
    db.add(pickup)
    db.flush()
    return pickup