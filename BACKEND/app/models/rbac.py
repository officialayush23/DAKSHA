# app/models/rbac.py

from pydantic import BaseModel
from typing import Optional

class RoleAssignRequest(BaseModel):
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None


class LocationCreate(BaseModel):
    name: str
    type: str # 'store' or 'warehouse'
    city: str
    address_line_1: str
    latitude: float
    longitude: float
    # Store specific
    store_code: Optional[str] = None
    # Warehouse specific
    warehouse_code: Optional[str] = None


    
class RoleRevoke(BaseModel):
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None