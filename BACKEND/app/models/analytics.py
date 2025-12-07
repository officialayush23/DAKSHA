from pydantic import BaseModel
from typing import Dict, Any, Optional


class FootprintCreate(BaseModel):
    user_id: Optional[str] = None
    guest_id: Optional[str] = None
    event_type: str
    event_data: Dict[str, Any]
