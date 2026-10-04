# app/core/background.py
"""
Fire-and-forget work that must never block a request.

`dispatch(task, *args)` sends a Celery task to the broker only when Celery is
enabled AND Redis answers; otherwise it runs the task's function in a small
thread pool. Before this, `refresh_user_preferences.delay()` hung add-to-cart
whenever the broker was down.
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings

log = logging.getLogger("daksha.background")
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="daksha-bg")


def submit(fn, *args, **kwargs):
    def _run():
        try:
            fn(*args, **kwargs)
        except Exception as e:  # background work must not crash the worker
            log.warning("background job %s failed: %s", getattr(fn, "__name__", fn), str(e)[:200])
    return _pool.submit(_run)


def dispatch(task, *args, **kwargs):
    """Run a Celery task via the broker if available, else in-process."""
    if settings.CELERY_ENABLED:
        from app.core.redis import redis_available
        if redis_available():
            try:
                return task.delay(*args, **kwargs)
            except Exception as e:
                log.warning("celery dispatch failed, running inline: %s", str(e)[:120])
    fn = getattr(task, "run", task)
    return submit(fn, *args, **kwargs)
