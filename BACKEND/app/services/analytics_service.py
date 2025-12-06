from app.database import supabase


class AnalyticsService:
    @staticmethod
    def log_footprint(payload: dict):
        supabase.table("user_footprints").insert(
            {
                "user_id": payload.get("user_id"),
                "event_type": payload["event_type"],
                "event_data": payload["event_data"],
            }
        ).execute()
