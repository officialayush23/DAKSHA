from pydantic import BaseModel
from typing import Dict, Any, Optional

class FootprintCreate(BaseModel):
    event_type: str
    event_data: Dict[str, Any]
    session_id: Optional[str] = None
