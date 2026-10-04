"""
Audit journal: every run, tool call, policy verdict and approval request is
written down. The SQL journal reuses DAKSHA's existing tables (agent_runs,
agent_actions, policy_decisions) and the new agent_approvals table, so the
admin "Agent Runs" page shows graph runs without changes.

Journal failures are logged and swallowed: auditing must never break a turn.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger("daksha.journal")


def _uuid_or_none(v):
    try:
        return str(uuid.UUID(str(v))) if v else None
    except (ValueError, TypeError):
        return None


def _dump(v: Any, limit: int = 4000):
    s = json.dumps(v, default=str)
    if len(s) > limit:
        return json.dumps({"_truncated": True, "preview": s[:limit]})
    return s


class Journal:
    def start_run(self, **kw) -> str: return str(uuid.uuid4())
    def finish_run(self, run_id: str, status: str, meta: Dict[str, Any]) -> None: ...
    def action(self, **kw) -> Optional[str]: return None
    def policy(self, **kw) -> None: ...
    def open_approval(self, *, approval_id: str, **kw) -> str: return approval_id
    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]: return None


class MemoryJournal(Journal):
    """In-process journal for tests and benchmarks."""

    def __init__(self) -> None:
        self.runs: Dict[str, Dict[str, Any]] = {}
        self.actions: List[Dict[str, Any]] = []
        self.policies: List[Dict[str, Any]] = []
        self.approvals: Dict[str, Dict[str, Any]] = {}

    def start_run(self, **kw):
        rid = str(uuid.uuid4())
        self.runs[rid] = {**kw, "status": "running"}
        return rid

    def finish_run(self, run_id, status, meta):
        self.runs.setdefault(run_id, {}).update(status=status, meta=meta)

    def action(self, **kw):
        aid = str(uuid.uuid4())
        self.actions.append({"id": aid, **kw})
        return aid

    def policy(self, **kw):
        self.policies.append(kw)

    def open_approval(self, *, approval_id, **kw):
        self.approvals.setdefault(approval_id, {"id": approval_id, "status": "pending", **kw})
        return approval_id

    def get_approval(self, approval_id):
        return self.approvals.get(approval_id)


class SqlJournal(Journal):
    def __init__(self, session_factory=None) -> None:
        if session_factory is None:
            from app.core.database import SessionLocal
            session_factory = SessionLocal
        self._sf = session_factory

    def _exec(self, sql: str, params: Dict[str, Any]) -> None:
        from sqlalchemy import text
        try:
            with self._sf() as db:
                db.execute(text(sql), params)
                db.commit()
        except Exception as e:
            log.warning("journal write failed: %s", str(e)[:300])

    def start_run(self, *, user_id, session_id, domain, trigger, channel, thread_id):
        rid = str(uuid.uuid4())
        self._exec("""
            INSERT INTO agent_runs (id, user_id, agent_name, agent_role, trigger_event, status, metadata, started_at)
            VALUES (:id, :u, 'Orchestrator', :role, :trig, 'running', CAST(:m AS jsonb), now())
        """, {"id": rid, "u": _uuid_or_none(user_id), "role": f"{domain}-graph", "trig": trigger,
              "m": _dump({"thread_id": thread_id, "chat_session_id": session_id, "channel": channel})})
        return rid

    def finish_run(self, run_id, status, meta):
        self._exec("""
            UPDATE agent_runs SET status = :s, completed_at = now(),
                   metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:m AS jsonb)
            WHERE id = :id
        """, {"id": run_id, "s": status, "m": _dump(meta, 20000)})

    def action(self, *, run_id, user_id, agent, tool, args, output, latency_ms, ok, error=None, model=None):
        aid = str(uuid.uuid4())
        self._exec("""
            INSERT INTO agent_actions (id, user_id, agent_run_id, agent_name, tool_name, tool_input,
                                       tool_output, model_used, latency_ms, success, error_message)
            VALUES (:id, :u, :r, :a, :t, CAST(:i AS jsonb), CAST(:o AS jsonb), :m, :l, :ok, :e)
        """, {"id": aid, "u": _uuid_or_none(user_id), "r": _uuid_or_none(run_id), "a": agent, "t": tool,
              "i": _dump(args), "o": _dump(output), "m": model, "l": int(latency_ms), "ok": ok,
              "e": (error or "")[:500] or None})
        return aid

    CATEGORY = {"offers": "offer", "post_purchase": "return", "fulfillment": "delivery", "checkout": "payment",
                "cart": "cart", "discovery": "discovery", "support": "support", "engagement": "engagement"}

    def policy(self, *, run_id, user_id, agent, rule, verdict, args, applied=None):
        applied = {"verdict": verdict, **({"normalized_args": applied} if applied else {})}
        verdict = self.CATEGORY.get(agent, "general")
        self._exec("""
            INSERT INTO policy_decisions (id, user_id, agent_run_id, agent_name, rule_name, rule_category,
                                          input_value, applied_value, was_overridden)
            VALUES (:id, :u, :r, :a, :rule, :cat, CAST(:i AS jsonb), CAST(:o AS jsonb), :ov)
        """, {"id": str(uuid.uuid4()), "u": _uuid_or_none(user_id), "r": _uuid_or_none(run_id), "a": agent,
              "rule": rule, "cat": verdict, "i": _dump(args), "o": _dump(applied or {}),
              "ov": "normalized_args" in applied})

    def open_approval(self, *, approval_id, thread_id, run_id, user_id, agent, tool, args, reason, rule, approver, summary):
        aid = approval_id
        self._exec("""
            INSERT INTO agent_approvals (id, thread_id, agent_run_id, user_id, agent, tool, args, reason,
                                         rule, approver_role, summary, status)
            VALUES (:id, :th, :r, :u, :a, :t, CAST(:args AS jsonb), :reason, :rule, :role, :sum, 'pending')
            ON CONFLICT (id) DO NOTHING
        """, {"id": aid, "th": thread_id, "r": _uuid_or_none(run_id), "u": _uuid_or_none(user_id), "a": agent,
              "t": tool, "args": _dump(args), "reason": reason, "rule": rule, "role": approver, "sum": summary})
        if approver == "staff":
            try:
                from app.api.routers.websocket_handoff import notify_admins_new_approval
                notify_admins_new_approval(aid, summary)
            except Exception:
                pass
        return aid

    def get_approval(self, approval_id):
        from sqlalchemy import text
        with self._sf() as db:
            r = db.execute(text("SELECT * FROM agent_approvals WHERE id = :id"), {"id": approval_id}).mappings().first()
            return dict(r) if r else None
