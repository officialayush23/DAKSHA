from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.database import supabase
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/")
async def list_my_notifications(user_id: str = Depends(get_current_user_id)):
    res = (
        supabase.table("user_notifications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


@router.post("/send-test")
async def send_test_notification(user_id: str = Depends(get_current_user_id)):
    """
    Simple endpoint to verify Redis + WebSocket pipeline.
    """
    record = await NotificationService.send_to_user(
        user_id, "Test Notification", "This is a test from /notifications/send-test", "debug"
    )
    return record


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str, user_id: str = Depends(get_current_user_id)):
    supabase.table("user_notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
    return {"status": "ok"}
