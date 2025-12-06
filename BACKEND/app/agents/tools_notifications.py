from langchain.tools import tool
from app.services.notification_service import NotificationService


@tool
async def send_notification_tool(user_id: str, title: str, body: str, type: str = "info") -> str:
    """
    Sends an in-app notification to the user and pushes via WebSocket.
    Use when you want to proactively confirm actions (order placed, coupon applied, etc.).
    """
    record = await NotificationService.send_to_user(user_id, title, body, type)
    return f"Notification sent with id={record['id']}"
