from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.services.rbac_service import RBACService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/rbac", tags=["Admin: RBAC"])


class AssignRoleRequest(BaseModel):
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None


@router.post("/assign")
async def assign_role(
    payload: AssignRoleRequest,
    user_id: str = Depends(get_current_user_id),
):
    return RBACService.assign_role(
        actor_user_id=user_id,
        target_user_id=payload.user_id,
        role=payload.role,
        store_id=payload.store_id,
        warehouse_id=payload.warehouse_id,
    )
