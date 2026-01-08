# app/routers/admin/ops_sla.py

from fastapi import APIRouter, Depends
from app.core.deps_ops import require_ops_user
from app.core.database import supabase

router = APIRouter(prefix="/admin/ops/sla", tags=["Admin SLA"])

@router.get("/breaches")
def list_breaches(ops=Depends(require_ops_user)):
    return (
        supabase.table("sla_breaches")
        .select("*")
        .order("breached_at", desc=True)
        .execute()
        .data
    )
