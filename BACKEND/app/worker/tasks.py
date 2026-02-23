# app/worker/tasks.py
from app.worker.celery_app import celery
from app.core.database import SessionLocal
from app.services.user_preference_service import build_user_preference_summary

from datetime import datetime
from app.models.models import CheckoutSession
from app.enums.db_enums import CheckoutStateEnum
from app.services.inventory_reservation_service import release_inventory


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
            release_inventory(db, checkout.cart_id)
            checkout.inventory_locked = False
            checkout.state = CheckoutStateEnum.CANCELLED

        db.commit()
    finally:
        db.close()