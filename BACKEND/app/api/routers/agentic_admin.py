# app/api/routers/agentic_admin.py
"""
Staff controls for the orchestration engine.

GET  /admin/agentic/approvals                 pending staff approvals (high-value refunds, proactive marketing ...)
POST /admin/agentic/approvals/{id}/decide     approve / reject → the paused graph run continues
GET  /admin/agentic/memories/{user_id}        what each agent remembers about a customer (per-agent namespaces)
POST /admin/agentic/proactive/run             run the proactive scan now
GET  /admin/agentic/proactive/recent          recent proactive triggers and outcomes
GET  /admin/agentic/graph                     Mermaid source of the live graph
GET  /admin/agentic/runs/{run_id}             plan + node trace of one graph run
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_db

router = APIRouter(prefix="/admin/agentic", tags=["Admin - Agentic"])


class Decision(BaseModel):
    approved: bool
    note: Optional[str] = Field(default=None, max_length=500)


def _jsonable(rows):
    out = []
    for r in rows:
        d = {}
        for k, v in dict(r).items():
            d[k] = v.isoformat() if hasattr(v, "isoformat") else (str(v) if k.endswith("id") and v is not None else v)
        out.append(d)
    return out


@router.get("/approvals")
def pending_approvals(status: str = "pending", db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.execute(text("""
        SELECT a.*, u.name AS customer_name, u.email AS customer_email FROM agent_approvals a
        LEFT JOIN users u ON u.id = a.user_id
        WHERE a.approver_role = 'staff' AND a.status = :s ORDER BY a.created_at DESC LIMIT 100
    """), {"s": status}).mappings().fetchall()
    return _jsonable(rows)


@router.post("/approvals/{approval_id}/decide")
async def decide(approval_id: str, payload: Decision, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    from app.agentic.runtime import resume
    row = db.execute(text("SELECT * FROM agent_approvals WHERE id = :id"), {"id": approval_id}).mappings().first()
    if not row or row["approver_role"] != "staff":
        raise HTTPException(404, "Approval not found")
    if row["status"] != "pending":
        raise HTTPException(409, f"Already {row['status']}")
    try:
        out = await resume(thread_id=row["thread_id"], approval_id=approval_id, approved=payload.approved,
                           by=str(admin.id), note=payload.note)
    except LookupError as e:
        raise HTTPException(409, str(e))
    if row["thread_id"] and not row["thread_id"].startswith("proactive:") and out.get("reply"):
        from app.services.chat_session_service import append_message
        append_message(db, row["thread_id"], "assistant", out["reply"], ui_data={"_agentic": {"plan": out.get("plan")}})
    return {"status": "approved" if payload.approved else "rejected", "result": {k: out.get(k) for k in ("reply", "plan", "approval")}}


@router.get("/memories/{user_id}")
def agent_memories(user_id: str, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.execute(text("""SELECT agent, kind, content, salience, created_at FROM agent_memories
                              WHERE user_id = :u ORDER BY agent, created_at DESC"""), {"u": user_id}).mappings().fetchall()
    by_agent = {}
    for r in _jsonable(rows):
        by_agent.setdefault(r["agent"], []).append(r)
    return by_agent


@router.post("/proactive/run")
async def run_proactive_now(admin=Depends(get_current_admin)):
    from app.agentic.commerce.proactive import scan_and_act
    return await scan_and_act()


@router.get("/proactive/recent")
def recent_proactive(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.execute(text("SELECT * FROM proactive_triggers ORDER BY created_at DESC LIMIT 100")).mappings().fetchall()
    return _jsonable(rows)


@router.get("/graph")
def graph(admin=Depends(get_current_admin)):
    from app.agentic.runtime import graph_mermaid
    return {"mermaid": graph_mermaid()}


@router.get("/runs/{run_id}")
def run_detail(run_id: str, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    run = db.execute(text("SELECT * FROM agent_runs WHERE id = :r"), {"r": run_id}).mappings().first()
    if not run:
        raise HTTPException(404, "Run not found")
    actions = db.execute(text("""SELECT agent_name, tool_name, tool_input, tool_output, latency_ms, success, error_message, created_at
                                 FROM agent_actions WHERE agent_run_id = :r ORDER BY created_at"""), {"r": run_id}).mappings().fetchall()
    policies = db.execute(text("""SELECT agent_name, rule_name, rule_category, input_value, applied_value, created_at
                                  FROM policy_decisions WHERE agent_run_id = :r ORDER BY created_at"""), {"r": run_id}).mappings().fetchall()
    return {"run": _jsonable([run])[0], "actions": _jsonable(actions), "policy_decisions": _jsonable(policies)}
