# app/services/analytics_service.py
from app.database import supabase
import logging

log = logging.getLogger("analytics")

class AnalyticsService:
    @staticmethod
    def log_footprint(user_id, event_type, event_data, session_id):
        payload = {
            "event_type": event_type,
            "event_data": event_data,
            "session_id": session_id
        }

        if user_id:
            payload["user_id"] = user_id

        try:
            supabase.table("user_footprints").insert(payload).execute()
        except Exception as e:
            log.error(f"Analytics insert failed: {e}")
