# app/routers/admin/ops_handoffs.py
from fastapi import APIRouter, Depends
from app.core.deps_ops import require_ops_user
from app.core.database import supabase

router = APIRouter(prefix="/admin/ops/handoffs", tags=["Admin Ops"])

@router.get("/")
def list_handoffs(status: str | None = None, ops=Depends(require_ops_user)):
    q = supabase.table("human_handoffs").select("*").order("created_at", desc=True)
    if status:
        q = q.eq("status", status)
    return q.execute().data


@router.post("/{handoff_id}/claim")
def claim_handoff(handoff_id: str, ops=Depends(require_ops_user)):
    supabase.rpc(
        "claim_handoff",
        {
            "p_handoff_id": handoff_id,
            "p_ops_user_id": ops["id"],
        },
    ).execute()
    return {"success": True}


@router.post("/{handoff_id}/resolve")
def resolve_handoff(handoff_id: str, ops=Depends(require_ops_user)):
    supabase.rpc(
        "resolve_handoff",
        {
            "p_handoff_id": handoff_id,
            "p_ops_user_id": ops["id"],
        },
    ).execute()
    return {"success": True}