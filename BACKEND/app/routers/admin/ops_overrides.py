# app/routers/admin/ops_overrides.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.deps_ops import require_ops_user
from app.core.database import supabase

router = APIRouter(prefix="/admin/ops/overrides", tags=["Admin Ops Overrides"])

class OpsOverrideCreate(BaseModel):
    target_type: str
    target_id: str
    action: str
    reason: str


@router.post("/")
def apply_override(payload: OpsOverrideCreate, ops=Depends(require_ops_user)):
    supabase.rpc(
        "apply_ops_override",
        {
            "p_ops_user_id": ops["id"],
            "p_target_type": payload.target_type,
            "p_target_id": payload.target_id,
            "p_action": payload.action,
            "p_reason": payload.reason,
        },
    ).execute()

    return {"success": True}
