# app/models/notifications.py

from pydantic import BaseModel
from typing import Optional


class NotificationCreate(BaseModel):
    user_id: str
    title: str
    body: str
    type: Optional[str] = "info"
