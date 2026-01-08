# app/services/notification_service.py

from app.core.database import supabase
from app.core.redis_bus import EventBus


class NotificationService:
    @staticmethod
    async def send_to_user(user_id: str, title: str, body: str, type: str = "info"):
        res = (
            supabase.table("user_notifications")
            .insert(
                {
                    "user_id": user_id,
                    "title": title,
                    "body": body,
                    "type": type,
                }
            )
            .execute()
        )
        record = res.data[0]
        await EventBus.notify_user(user_id, "notification", record)
        return record
