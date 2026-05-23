# app/worker/celery_app.py
from celery import Celery
from app.core.config import settings

celery = Celery(
    "retail_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery.conf.task_routes = {
    "app.worker.tasks.*": {"queue": "ai"}
}

# ── Beat schedule ─────────────────────────────────────────────────────────────
from celery.schedules import crontab

celery.conf.beat_schedule = {
    # Release checkout reservations that expired — every 15 minutes
    "release-expired-reservations": {
        "task": "app.worker.tasks.release_expired_reservations",
        "schedule": crontab(minute="*/15"),
    },
    # Proactive wishlist discount offers — every day at 10:00 AM UTC
    "proactive-wishlist-offers": {
        "task": "app.worker.tasks.send_proactive_wishlist_offers",
        "schedule": crontab(hour=10, minute=0),
    },
}