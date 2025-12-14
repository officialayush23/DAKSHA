# app/models/channels.py

from pydantic import BaseModel
from typing import Optional


class ChannelMessage(BaseModel):
    channel_type: str  # 'web' | 'kiosk' | 'whatsapp'
    channel_id: str    # cookie / device_id / phone / kiosk_id
    message: str
    locale: Optional[str] = "en"
