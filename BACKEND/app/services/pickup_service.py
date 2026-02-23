# app/services/pickup_service.py
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.models import Pickup


def assign_pickup_store(
    db: Session,
    order_id,
    store_id,
    scheduled_time,
):
    pickup = Pickup(
        order_id=order_id,
        store_id=store_id,
        scheduled_time=scheduled_time,
        status="pending",
    )
    db.add(pickup)
    db.commit()
    return pickup