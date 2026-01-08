# app/routers/admin/ops_agents.py

from fastapi import APIRouter, Depends, Query
from app.core.deps_ops import require_ops_user
from app.core.database import supabase

router = APIRouter(prefix="/admin/ops/agents", tags=["Admin Agents"])


@router.get("/runs")
def list_agent_runs(ops=Depends(require_ops_user)):
    return (
        supabase
        .table("agent_runs")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )


@router.get("/runs/{run_id}")
def get_agent_run(run_id: str, ops=Depends(require_ops_user)):
    return (
        supabase
        .table("agent_runs")
        .select("*")
        .eq("id", run_id)
        .maybe_single()
        .execute()
        .data
    )


@router.get("/proposals")
def list_proposals(
    conversation_id: str = Query(...),
    ops=Depends(require_ops_user),
):
    # Step 1: get agent_run_ids for this conversation
    runs = (
        supabase
        .table("agent_runs")
        .select("id")
        .eq("conversation_id", conversation_id)
        .execute()
        .data
    )

    if not runs:
        return []

    run_ids = [r["id"] for r in runs]

    # Step 2: fetch proposals for those runs
    return (
        supabase
        .table("agent_proposals")
        .select("*")
        .in_("agent_run_id", run_ids)
        .order("created_at", desc=True)
        .execute()
        .data
    )
