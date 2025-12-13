from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.core.rbac import require_role
from app.services.role_service import RoleService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin/roles", tags=["Admin: Roles"])


class AssignRolePayload(BaseModel):
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None


@router.post("/assign")
async def assign_role(
    payload: AssignRolePayload,
    admin_id: str = Depends(get_current_user_id),
    _ = Depends(require_role("super_admin", "admin")),
):
    """
    Assign scoped or global roles.
    """
    return RoleService.assign_role(
        admin_id=admin_id,
        user_id=payload.user_id,
        role=payload.role,
        store_id=payload.store_id,
        warehouse_id=payload.warehouse_id,
    )
