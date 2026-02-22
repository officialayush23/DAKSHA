# app/worker/tasks.py
from app.worker.celery_app import celery
from app.core.database import SessionLocal
from app.services.user_preference_service import build_user_preference_summary


@celery.task(bind=True, max_retries=3)
def refresh_user_preferences(self, user_id: str):
    db = SessionLocal()
    try:
        build_user_preference_summary(db, user_id)
    finally:
        db.close()