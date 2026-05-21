# app/api/routers/agent_runs_admin.py
"""
Admin API for agent run traces and action logs.
Powers the AgentRuns.jsx page with full step-by-step tool call details.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.deps import get_db, get_current_admin
from app.models.models import AgentRun, AgentAction, PolicyDecision

router = APIRouter(prefix="/admin/agent-runs", tags=["Admin – Agent Runs"])


@router.get("")
def list_agent_runs(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    session_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """List agent runs with pagination. Filterable by session or agent."""
    q = db.query(AgentRun).order_by(AgentRun.started_at.desc())
    if session_id:
        q = q.filter(AgentRun.session_id == UUID(session_id))
    if agent_name:
        q = q.filter(AgentRun.agent_name == agent_name)

    total = q.count()
    runs = q.offset(offset).limit(limit).all()

    return {
        "total": total,
        "runs": [
            {
                "id": str(r.id),
                "session_id": str(r.session_id) if r.session_id else None,
                "agent_name": r.agent_name,
                "status": r.status,
                "confidence": r.confidence,
                "error_message": r.error_message,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_ms": (
                    int((r.completed_at - r.started_at).total_seconds() * 1000)
                    if r.completed_at and r.started_at else None
                ),
            }
            for r in runs
        ],
    }


@router.get("/{run_id}/actions")
def get_run_actions(
    run_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """
    Get every tool call action for a specific agent run.
    Returns the full step-by-step trace: tool name, input, output, latency, model.
    """
    actions = (
        db.query(AgentAction)
        .filter(AgentAction.agent_run_id == UUID(run_id))
        .order_by(AgentAction.created_at.asc())
        .all()
    )
    return {
        "run_id": run_id,
        "action_count": len(actions),
        "actions": [
            {
                "id": str(a.id),
                "agent_name": a.agent_name,
                "tool_name": a.tool_name,
                "tool_input": a.tool_input,
                "tool_output": a.tool_output,
                "model_used": a.model_used,
                "latency_ms": a.latency_ms,
                "success": a.success,
                "error_message": a.error_message,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ],
    }


@router.get("/actions/recent")
def get_recent_actions(
    limit: int = Query(100, le=500),
    agent_name: Optional[str] = None,
    tool_name: Optional[str] = None,
    success_only: bool = False,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Recent tool call actions across all sessions — live activity feed."""
    q = db.query(AgentAction).order_by(AgentAction.created_at.desc())
    if agent_name:
        q = q.filter(AgentAction.agent_name == agent_name)
    if tool_name:
        q = q.filter(AgentAction.tool_name == tool_name)
    if success_only:
        q = q.filter(AgentAction.success == True)

    actions = q.limit(limit).all()
    return [
        {
            "id": str(a.id),
            "session_id": str(a.session_id) if a.session_id else None,
            "agent_name": a.agent_name,
            "tool_name": a.tool_name,
            "model_used": a.model_used,
            "latency_ms": a.latency_ms,
            "success": a.success,
            "error_message": a.error_message,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in actions
    ]


@router.get("/policy-decisions")
def get_policy_decisions(
    limit: int = Query(100, le=500),
    rule_category: Optional[str] = None,
    overrides_only: bool = False,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Policy rule applications — shows what the agents decided and what policy allowed."""
    q = db.query(PolicyDecision).order_by(PolicyDecision.created_at.desc())
    if rule_category:
        q = q.filter(PolicyDecision.rule_category == rule_category)
    if overrides_only:
        q = q.filter(PolicyDecision.was_overridden == True)

    decisions = q.limit(limit).all()
    return [
        {
            "id": str(d.id),
            "agent_name": d.agent_name,
            "rule_name": d.rule_name,
            "rule_category": d.rule_category,
            "input_value": d.input_value,
            "applied_value": d.applied_value,
            "was_overridden": d.was_overridden,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in decisions
    ]
