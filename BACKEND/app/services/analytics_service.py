# app/services/analytics_service.py
from app.core.database import supabase_admin
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
            # Use user_facts table (not user_footprints)
            # Note: In Supabase v2, insert() already returns data - no need for .select()
            supabase_admin.table("user_facts").insert(payload).execute()
        except Exception as e:
            log.error(f"Analytics insert failed: {e}")
