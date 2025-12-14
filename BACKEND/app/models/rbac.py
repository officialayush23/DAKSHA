# app/models/rbac.py

from pydantic import BaseModel
from typing import Optional

class RoleAssignRequest(BaseModel):
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None
