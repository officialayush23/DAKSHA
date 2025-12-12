# app/services/analytics_service.py
import logging
from app.database import supabase

logger = logging.getLogger("daksha.analytics")


class AnalyticsService:
    @staticmethod
    def log_footprint(user_id: str | None, event_type: str, event_data: dict, session_id: str | None = None):
        """
        Fire-and-forget insert into user_footprints (jsonb).
        Always swallow DB errors to keep UX snappy.
        """
        try:
            payload = {"event_type": event_type, "event_data": event_data}
            if user_id:
                payload["user_id"] = user_id
            if session_id:
                payload["session_id"] = session_id
            res = supabase.table("user_footprints").insert(payload).execute()
            if getattr(res, "error", None):
                logger.error("Analytics DB error: %s", res.error)
        except Exception:
            logger.exception("Failed to log footprint")
