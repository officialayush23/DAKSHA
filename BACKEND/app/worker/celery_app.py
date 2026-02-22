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