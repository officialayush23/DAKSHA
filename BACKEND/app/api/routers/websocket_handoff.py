# app/api/routers/websocket_handoff.py
"""
Human handoff over WebSockets.

  WS /ws/customer/{chat_session_id}?token=...   customer side (Supabase or kiosk token, must own the chat)
  WS /ws/admin/lobby?token=...                   staff dashboard: new handoffs + approval requests appear live
  WS /ws/admin/{handoff_id}?token=...            staff side of one conversation (admin role required)
  GET /ws/admin/handoffs/open                    open handoffs (admin)

When the graph escalates (customer asks for a person, repeated failures, or
a critical complaint), an agent_handoffs row is opened for the chat thread.
While it is open, /chat/ relays customer messages here instead of running the
agents. Resolving the handoff hands the thread back to the agents, which see
the whole human exchange in the chat history.

Connections are tracked in-process (fine for one instance). Messages are
persisted to handoff_messages and chat_messages, so nothing is lost if a
socket drops.
"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import verify_token_ws
from app.core.database import SessionLocal
from app.core.deps import get_current_admin, get_db

router = APIRouter(prefix="/ws", tags=["websocket-handoff"])


class ConnectionManager:
    def __init__(self):
        self.customers: Dict[str, Set[WebSocket]] = {}
        self.admins: Dict[str, Set[WebSocket]] = {}
        self.lobby: Set[WebSocket] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def _send(self, conns: Set[WebSocket], payload: dict):
        for ws in list(conns):
            try:
                await ws.send_json(payload)
            except Exception:
                conns.discard(ws)

    async def to_customer(self, chat_id: str, payload: dict):
        await self._send(self.customers.get(chat_id, set()), payload)

    async def to_admins(self, handoff_id: str, payload: dict):
        await self._send(self.admins.get(handoff_id, set()), payload)

    async def to_lobby(self, payload: dict):
        await self._send(self.lobby, payload)

    def broadcast_lobby_threadsafe(self, payload: dict):
        """Called from worker threads (graph nodes) to ping the staff dashboard."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.to_lobby(payload), self.loop)


manager = ConnectionManager()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _persist(db: Session, handoff_id: str, chat_id: str, speaker: str, message: str, admin_id: Optional[str] = None):
    db.execute(text("""INSERT INTO handoff_messages (id, handoff_id, speaker, message, admin_id)
                       VALUES (:id, :h, :sp, :m, :a)"""),
               {"id": str(uuid.uuid4()), "h": handoff_id, "sp": speaker, "m": message, "a": admin_id})
    if speaker == "admin":
        db.execute(text("""INSERT INTO chat_messages (id, session_id, role, content, created_at)
                           VALUES (:id, :s, 'staff', :m, now())"""), {"id": str(uuid.uuid4()), "s": chat_id, "m": message})
    db.commit()


def notify_admins_new_handoff(handoff_id: str):
    manager.broadcast_lobby_threadsafe({"type": "handoff_opened", "handoff_id": handoff_id, "at": _now()})


def notify_admins_new_approval(approval_id: str, summary: str):
    manager.broadcast_lobby_threadsafe({"type": "approval_requested", "approval_id": approval_id, "summary": summary, "at": _now()})


async def relay_customer_message(db: Session, handoff_id: str, chat_id: str, message: str):
    """Customer typed in /chat/ while a human owns the thread (chat_messages row already written)."""
    db.execute(text("""INSERT INTO handoff_messages (id, handoff_id, speaker, message) VALUES (:id, :h, 'user', :m)"""),
               {"id": str(uuid.uuid4()), "h": handoff_id, "m": message})
    db.commit()
    await manager.to_admins(handoff_id, {"type": "message", "speaker": "user", "message": message, "timestamp": _now()})


async def relay_admin_message(db: Session, handoff_id: str, chat_id: str, message: str, admin_id: str):
    _persist(db, handoff_id, chat_id, "admin", message, admin_id)
    payload = {"type": "message", "speaker": "admin", "message": message, "timestamp": _now()}
    await manager.to_customer(chat_id, payload)
    await manager.to_admins(handoff_id, payload)


def _is_admin(db: Session, claims: Optional[dict]) -> Optional[str]:
    if not claims or claims.get("aud") != "authenticated":
        return None
    row = db.execute(text("SELECT id, role FROM users WHERE id = :u"), {"u": claims.get("sub")}).first()
    return str(row.id) if row and row.role == "admin" else None


# ── Customer ──────────────────────────────────────────────────────────────────

@router.websocket("/customer/{chat_session_id}")
async def customer_ws(websocket: WebSocket, chat_session_id: str, token: Optional[str] = Query(default=None)):
    claims = await verify_token_ws(websocket, token)
    with SessionLocal() as db:
        owner = db.execute(text("SELECT user_id FROM chat_sessions WHERE id = :s"), {"s": chat_session_id}).first() if claims else None
    if not claims or not owner or str(owner.user_id) != claims.get("sub"):
        await websocket.close(code=4401)
        return
    manager.loop = asyncio.get_running_loop()
    await websocket.accept()
    manager.customers.setdefault(chat_session_id, set()).add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg = (data.get("message") or "").strip()
            if not msg:
                continue
            with SessionLocal() as db:
                h = db.execute(text("""SELECT id FROM agent_handoffs WHERE chat_session_id = :s
                                       AND status IN ('open','in_progress') LIMIT 1"""), {"s": chat_session_id}).first()
                if not h:
                    await websocket.send_json({"type": "info", "message": "No human is on this chat right now; send it through the assistant."})
                    continue
                db.execute(text("""INSERT INTO chat_messages (id, session_id, role, content, created_at)
                                   VALUES (:id, :s, 'user', :m, now())"""), {"id": str(uuid.uuid4()), "s": chat_session_id, "m": msg})
                db.commit()
                await relay_customer_message(db, str(h.id), chat_session_id, msg)
            await websocket.send_json({"type": "ack", "message": msg, "timestamp": _now()})
    except WebSocketDisconnect:
        manager.customers.get(chat_session_id, set()).discard(websocket)


# ── Staff ─────────────────────────────────────────────────────────────────────

@router.websocket("/admin/lobby")
async def admin_lobby(websocket: WebSocket, token: Optional[str] = Query(default=None)):
    claims = await verify_token_ws(websocket, token)
    with SessionLocal() as db:
        if not _is_admin(db, claims):
            await websocket.close(code=4403)
            return
    manager.loop = asyncio.get_running_loop()
    await websocket.accept()
    manager.lobby.add(websocket)
    try:
        while True:
            await websocket.receive_text()   # keepalive pings
    except WebSocketDisconnect:
        manager.lobby.discard(websocket)


@router.websocket("/admin/{handoff_id}")
async def admin_ws(websocket: WebSocket, handoff_id: str, token: Optional[str] = Query(default=None)):
    claims = await verify_token_ws(websocket, token)
    with SessionLocal() as db:
        admin_id = _is_admin(db, claims)
        h = db.execute(text("SELECT * FROM agent_handoffs WHERE id = :h"), {"h": handoff_id}).mappings().first() if admin_id else None
    if not admin_id or not h:
        await websocket.close(code=4403)
        return
    manager.loop = asyncio.get_running_loop()
    await websocket.accept()
    manager.admins.setdefault(handoff_id, set()).add(websocket)
    chat_id = str(h["chat_session_id"]) if h["chat_session_id"] else None
    with SessionLocal() as db:
        hist = db.execute(text("""SELECT role, content, created_at FROM chat_messages WHERE session_id = :s
                                  ORDER BY created_at"""), {"s": chat_id}).fetchall() if chat_id else []
    await websocket.send_json({
        "type": "history", "handoff_id": handoff_id, "session_id": chat_id, "user_id": str(h["user_id"]) if h["user_id"] else None,
        "reason": h["reason"], "summary": h["summary"],
        "messages": [{"speaker": {"assistant": "ai", "staff": "admin"}.get(r.role, r.role), "message": r.content,
                      "created_at": r.created_at.isoformat() if r.created_at else None} for r in hist],
    })
    try:
        while True:
            data = await websocket.receive_json()
            kind = data.get("type", "message")
            with SessionLocal() as db:
                if kind == "message" and (data.get("message") or "").strip() and chat_id:
                    await relay_admin_message(db, handoff_id, chat_id, data["message"].strip(), admin_id)
                elif kind == "assign":
                    db.execute(text("UPDATE agent_handoffs SET assigned_to_admin_id = :a, status = 'in_progress' WHERE id = :h"),
                               {"a": admin_id, "h": handoff_id})
                    db.commit()
                    await manager.to_admins(handoff_id, {"type": "assigned", "admin_id": admin_id})
                elif kind == "resolve":
                    db.execute(text("""UPDATE agent_handoffs SET status = 'resolved', resolved_at = now(), resolved_by = :a,
                                       resolution_note = :n WHERE id = :h"""), {"a": admin_id, "n": data.get("note", ""), "h": handoff_id})
                    db.commit()
                    msg = "Our team has wrapped up. I'm back to help with anything else."
                    if chat_id:
                        db.execute(text("""INSERT INTO chat_messages (id, session_id, role, content, created_at)
                                           VALUES (:id, :s, 'assistant', :m, now())"""), {"id": str(uuid.uuid4()), "s": chat_id, "m": msg})
                        db.commit()
                        await manager.to_customer(chat_id, {"type": "handoff_resolved", "message": msg})
                    await manager.to_admins(handoff_id, {"type": "handoff_resolved", "message": "Resolved. The assistant has the conversation again."})
    except WebSocketDisconnect:
        manager.admins.get(handoff_id, set()).discard(websocket)


@router.get("/admin/handoffs/open")
def get_open_handoffs(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    rows = db.execute(text("""SELECT id, session_id, chat_session_id, user_id, from_agent_name, reason, summary, status,
                                     escalation_level, created_at FROM agent_handoffs
                              WHERE status IN ('open','in_progress') ORDER BY created_at DESC LIMIT 50""")).mappings().fetchall()
    return [{**{k: (str(v) if k.endswith("id") and v else v) for k, v in r.items()},
             "session_id": str(r["chat_session_id"] or r["session_id"] or "") or None,
             "created_at": r["created_at"].isoformat() if r["created_at"] else None} for r in rows]
