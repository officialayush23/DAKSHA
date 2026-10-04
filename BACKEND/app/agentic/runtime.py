"""
Runtime glue between FastAPI and the orchestration graph.

- one compiled graph per process, with a Postgres checkpointer (falls back to
  in-memory if LANGGRAPH_DB_URL is missing), so conversations and paused
  approvals survive restarts and are shared by every channel
- run_turn():   one user message → plan → agents → reply
- resume():     a human approved/rejected a paused action → continue the run
- run_proactive(): a scheduler trigger → the same graph in "proactive" mode
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from langgraph.types import Command

from app.agentic.core.graph import Engine
from app.agentic.core.journal import SqlJournal
from app.agentic.core.memory import SqlMemoryStore

log = logging.getLogger("daksha.runtime")

_engine: Optional[Engine] = None
_graph = None
_pool = None
_lock = asyncio.Lock()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        from app.core.config import settings
        if settings.DAKSHA_DOMAIN != "commerce":
            raise RuntimeError(f"unknown domain pack {settings.DAKSHA_DOMAIN}")
        from app.agentic.commerce.pack import build_pack
        _engine = Engine(build_pack(), memory=SqlMemoryStore(), journal=SqlJournal())
    return _engine


async def get_graph():
    """Compile once; reuse a pooled Postgres checkpointer."""
    global _graph, _pool
    if _graph is not None:
        return _graph
    async with _lock:
        if _graph is not None:
            return _graph
        from app.core.config import settings
        engine = get_engine()
        url = settings.LANGGRAPH_DB_URL or settings.DATABASE_URL
        checkpointer = None
        try:
            # Sync saver + graph.invoke() in a worker thread. All nodes are sync, and
            # interrupt() needs the run context, which async-in-executor loses on Python < 3.11.
            from langgraph.checkpoint.postgres import PostgresSaver
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool

            def _open():
                pool = ConnectionPool(url, max_size=8, open=True, timeout=20,
                                      kwargs={"autocommit": True, "prepare_threshold": None, "row_factory": dict_row})
                saver = PostgresSaver(pool)
                saver.setup()
                return pool, saver
            _pool, checkpointer = await asyncio.to_thread(_open)
        except Exception as e:
            log.warning("Postgres checkpointer unavailable (%s); using in-memory checkpoints", str(e)[:200])
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()
        _graph = engine.build().compile(checkpointer=checkpointer)
        return _graph


def _shape(state: Dict[str, Any], elapsed_ms: float) -> Dict[str, Any]:
    interrupts = state.get("__interrupt__") or []
    approval = interrupts[0].value if interrupts else None
    plan = state.get("plan") or []
    trace = state.get("trace") or []
    agents_used = []
    for st in plan:
        if st["agent"] not in agents_used:
            agents_used.append(st["agent"])
    reply = state.get("reply") or ""
    if approval and approval.get("approver") == "customer":
        reply = approval.get("reason") or "Please confirm to continue."
    elif approval:
        reply = (reply or "") + ("\n\n" if reply else "") + "I've sent this to our team for approval and will continue as soon as they respond."
    return {
        "reply": reply,
        "ui": state.get("ui"),
        "plan": [{k: st.get(k) for k in ("agent", "objective", "status", "result")} for st in plan],
        "agents": agents_used,
        "trace": trace,
        "approval": approval,
        "handoff": state.get("handoff"),
        "run_id": state.get("run_id"),
        "latency_ms": round(elapsed_ms, 1),
    }


async def run_turn(*, thread_id: str, user_id: str, session_id: str, message: str, channel: str = "web",
                   store_id: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, Any]:
    graph = await get_graph()
    engine = get_engine()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit()}
    snap = await asyncio.to_thread(graph.get_state, cfg)
    if snap and snap.next:
        # a previous run is paused on an approval; a new message supersedes it
        pending = (snap.tasks[0].interrupts[0].value if snap.tasks and snap.tasks[0].interrupts else None)
        if pending:
            _decide_sql(pending["approval_id"], approved=False, by=user_id, note="superseded by a new message")
            await asyncio.to_thread(graph.invoke, Command(resume={"approved": False, "by": "system", "note": "superseded"}), cfg)
    t0 = time.perf_counter()
    state = await asyncio.to_thread(graph.invoke, {
        "thread_id": thread_id, "user_id": user_id, "session_id": session_id, "channel": channel,
        "store_id": store_id, "mode": "chat", "input": message, "image_url": image_url,
    }, cfg)
    return _shape(state, (time.perf_counter() - t0) * 1000)


def _decide_sql(approval_id: str, *, approved: bool, by: Optional[str], note: Optional[str]) -> None:
    from sqlalchemy import text
    from app.core.database import SessionLocal
    with SessionLocal() as db:
        db.execute(text("""UPDATE agent_approvals SET status = :s, decided_by = :by, decision_note = :n, decided_at = now()
                           WHERE id = :id AND status = 'pending'"""),
                   {"s": "approved" if approved else "rejected", "by": by if by and len(str(by)) == 36 else None,
                    "n": note, "id": approval_id})
        db.commit()


async def resume(*, thread_id: str, approval_id: str, approved: bool, by: Optional[str], note: Optional[str] = None) -> Dict[str, Any]:
    graph = await get_graph()
    engine = get_engine()
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit()}
    snap = await asyncio.to_thread(graph.get_state, cfg)
    pending = (snap.tasks[0].interrupts[0].value if snap and snap.tasks and snap.tasks[0].interrupts else None)
    if not pending or pending.get("approval_id") != approval_id:
        raise LookupError("This request is no longer waiting for a decision.")
    _decide_sql(approval_id, approved=approved, by=by, note=note)
    t0 = time.perf_counter()
    state = await asyncio.to_thread(graph.invoke, Command(resume={"approved": approved, "by": by, "note": note}), cfg)
    return _shape(state, (time.perf_counter() - t0) * 1000)


async def run_proactive(*, user_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
    graph = await get_graph()
    engine = get_engine()
    thread_id = f"proactive:{trigger['type']}:{user_id}:{trigger.get('key', '')}"
    cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": engine.recursion_limit()}
    t0 = time.perf_counter()
    state = await asyncio.to_thread(graph.invoke, {
        "thread_id": thread_id, "user_id": user_id, "session_id": None, "channel": "proactive",
        "store_id": None, "mode": "proactive", "trigger": trigger, "input": "",
    }, cfg)
    return _shape(state, (time.perf_counter() - t0) * 1000)


def graph_mermaid() -> str:
    return get_engine().build().compile().get_graph().draw_mermaid()
