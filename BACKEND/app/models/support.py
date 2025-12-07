from pydantic import BaseModel
from typing import Optional


class TicketCreate(BaseModel):
    user_id: str
    order_id: Optional[str] = None
    issue_summary: str
    conversation_summary: str
    sentiment_score: float
