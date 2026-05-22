# app/api/routers/websocket_handoff.py
"""
WebSocket-based Human Handoff System
══════════════════════════════════════════════════════════════════════════
Two WebSocket endpoints:
  WS /ws/customer/{session_id}  — customer's chat UI connects here
  WS /ws/admin/{handoff_id}     — admin panel connects here

When an agent calls request_human_handoff:
  1. AgentHandoff record created (REST, already exists)
  2. Customer's WS is already open → they see a "connecting to human" message
  3. Admin opens Handoffs page → connects to WS /ws/admin/{handoff_id}
  4. Both ends joined to the same Redis pub/sub channel: ws:room:{session_id}
  5. Any message from either end → saved to handoff_messages + pub/sub → other end
  6. Admin clicks Resolve → handoff.status = resolved → AI resumes
══════════════════════════════════════════════════════════════════════════
"""
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Set

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.config import settings
from app.core.auth import verify_token_ws          # you'll wire this below
from app.models.models import AgentHandoff, HandoffMessage, UserSession, Conversation
from app.enums.db_enums import ComplaintStatusEnum, ChannelEnum

router = APIRouter(prefix="/ws", tags=["websocket-handoff"])

# ── Redis pub/sub helper ───────────────────────────────────────────────────────

def _room_channel(session_id: str) -> str:
    return f"ws:room:{session_id}"


async def get_redis() -> aioredis.Redis:
    return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)


# ── In-memory connection registry (per process — fine for single-instance) ────
# For multi-instance: replace with Redis pub/sub subscriber per connection

class ConnectionManager:
    def __init__(self):
        # session_id → set of customer WebSocket connections
        self._customer_connections: Dict[str, Set[WebSocket]] = {}
        # handoff_id → set of admin WebSocket connections
        self._admin_connections: Dict[str, Set[WebSocket]] = {}

    # ── Customer ──────────────────────────────────────────────────────────────
    def add_customer(self, session_id: str, ws: WebSocket):
        self._customer_connections.setdefault(session_id, set()).add(ws)

    def remove_customer(self, session_id: str, ws: WebSocket):
        if session_id in self._customer_connections:
            self._customer_connections[session_id].discard(ws)

    async def send_to_customer(self, session_id: str, payload: dict):
        for ws in list(self._customer_connections.get(session_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                self._customer_connections[session_id].discard(ws)

    # ── Admin ─────────────────────────────────────────────────────────────────
    def add_admin(self, handoff_id: str, ws: WebSocket):
        self._admin_connections.setdefault(handoff_id, set()).add(ws)

    def remove_admin(self, handoff_id: str, ws: WebSocket):
        if handoff_id in self._admin_connections:
            self._admin_connections[handoff_id].discard(ws)

    async def send_to_admins(self, handoff_id: str, payload: dict):
        for ws in list(self._admin_connections.get(handoff_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                self._admin_connections[handoff_id].discard(ws)


manager = ConnectionManager()


# ── DB helpers ────────────────────────────────────────────────────────────────

def _save_handoff_message(
    db: Session,
    handoff_id: uuid.UUID,
    session_id: uuid.UUID,
    speaker: str,
    message: str,
    admin_id: uuid.UUID | None = None,
) -> "HandoffMessage":
    msg = HandoffMessage(
        handoff_id=handoff_id,
        session_id=session_id,
        speaker=speaker,
        message=message,
        admin_id=admin_id,
    )
    db.add(msg)
    # Also persist to conversations table for AI context after handoff resolves
    conv = Conversation(
        session_id=session_id,
        channel=ChannelEnum.web,
        speaker=speaker,
        message=message,
        intent="human_handoff",
    )
    db.add(conv)
    db.commit()
    db.refresh(msg)
    return msg


def _get_handoff_history(db: Session, handoff_id: uuid.UUID) -> list:
    msgs = (
        db.query(HandoffMessage)
        .filter(HandoffMessage.handoff_id == handoff_id)
        .order_by(HandoffMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(m.id),
            "speaker": m.speaker,
            "message": m.message,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


# ── Customer WebSocket ─────────────────────────────────────────────────────────

@router.websocket("/customer/{session_id}")
async def customer_ws(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db),
):
    """
    Customer connects here. If a handoff is active for their session,
    messages are relayed to the admin. Otherwise messages are ignored
    (the AI handles them via the REST /chat endpoint).
    """
    await websocket.accept()
    manager.add_customer(session_id, websocket)

    # Find active handoff for this session
    session = db.query(UserSession).filter(
        UserSession.id == uuid.UUID(session_id)
    ).first()

    try:
        while True:
            data = await websocket.receive_json()
            message_text = data.get("message", "").strip()
            if not message_text:
                continue

            # Only relay if handoff is active
            if session and session.active_handoff_id:
                handoff_id = str(session.active_handoff_id)
                _save_handoff_message(
                    db,
                    handoff_id=session.active_handoff_id,
                    session_id=uuid.UUID(session_id),
                    speaker="user",
                    message=message_text,
                )
                payload = {
                    "type": "message",
                    "speaker": "user",
                    "message": message_text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "session_id": session_id,
                }
                await manager.send_to_admins(handoff_id, payload)
                # Echo back to customer (acknowledge receipt)
                await websocket.send_json({
                    "type": "ack",
                    "message": message_text,
                    "timestamp": payload["timestamp"],
                })
    except WebSocketDisconnect:
        manager.remove_customer(session_id, websocket)


# ── Admin WebSocket ────────────────────────────────────────────────────────────

@router.websocket("/admin/{handoff_id}")
async def admin_ws(
    websocket: WebSocket,
    handoff_id: str,
    db: Session = Depends(get_db),
):
    """
    Admin connects here to handle a specific handoff.
    On connect: sends full conversation history.
    On message: relays to the customer.
    On resolve event: marks handoff resolved, AI resumes.
    """
    await websocket.accept()
    manager.add_admin(handoff_id, websocket)

    handoff = db.query(AgentHandoff).filter(
        AgentHandoff.id == uuid.UUID(handoff_id)
    ).first()

    if not handoff:
        await websocket.send_json({"type": "error", "message": "Handoff not found."})
        await websocket.close()
        return

    session_id = str(handoff.session_id) if handoff.session_id else None

    # Send full history on connect
    history = _get_handoff_history(db, uuid.UUID(handoff_id))
    await websocket.send_json({
        "type": "history",
        "handoff_id": handoff_id,
        "session_id": session_id,
        "user_id": str(handoff.user_id) if handoff.user_id else None,
        "reason": handoff.reason,
        "summary": handoff.summary,
        "messages": history,
    })

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "message")

            # ── Admin sends a chat message ─────────────────────────────────
            if event_type == "message":
                message_text = data.get("message", "").strip()
                admin_id_str = data.get("admin_id")
                if not message_text:
                    continue

                admin_id = uuid.UUID(admin_id_str) if admin_id_str else None
                _save_handoff_message(
                    db,
                    handoff_id=uuid.UUID(handoff_id),
                    session_id=uuid.UUID(session_id) if session_id else None,
                    speaker="admin",
                    message=message_text,
                    admin_id=admin_id,
                )
                payload = {
                    "type": "message",
                    "speaker": "admin",
                    "message": message_text,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                # Send to customer
                if session_id:
                    await manager.send_to_customer(session_id, payload)
                # Echo to all admin tabs watching this handoff
                await manager.send_to_admins(handoff_id, payload)

            # ── Admin resolves the handoff ─────────────────────────────────
            elif event_type == "resolve":
                admin_id_str = data.get("admin_id")
                note = data.get("note", "")

                handoff.status = ComplaintStatusEnum.resolved
                handoff.resolved_at = datetime.now(timezone.utc)
                handoff.resolved_by = uuid.UUID(admin_id_str) if admin_id_str else None
                handoff.resolution_note = note

                # Clear pending_human_input on the session
                if session_id:
                    session = db.query(UserSession).filter(
                        UserSession.id == uuid.UUID(session_id)
                    ).first()
                    if session:
                        session.active_handoff_id = None
                        ctx = dict(session.context or {})
                        ctx["pending_human_input"] = False
                        session.context = ctx

                db.commit()

                # Notify customer that AI is resuming
                if session_id:
                    await manager.send_to_customer(session_id, {
                        "type": "handoff_resolved",
                        "message": "Our support team has resolved your query. I'll take it from here! How can I help you?",
                    })
                # Notify admin
                await manager.send_to_admins(handoff_id, {
                    "type": "handoff_resolved",
                    "message": f"Handoff resolved by admin.",
                })

            # ── Admin assigns the handoff ──────────────────────────────────
            elif event_type == "assign":
                admin_id_str = data.get("admin_id")
                if admin_id_str:
                    handoff.assigned_to_admin_id = uuid.UUID(admin_id_str)
                    handoff.status = ComplaintStatusEnum.in_progress
                    db.commit()
                    await manager.send_to_admins(handoff_id, {
                        "type": "assigned",
                        "admin_id": admin_id_str,
                    })

    except WebSocketDisconnect:
        manager.remove_admin(handoff_id, websocket)


# ── REST: Get open handoffs list (for admin panel polling on load) ────────────

@router.get("/admin/handoffs/open")
def get_open_handoffs(db: Session = Depends(get_db)):
    """Returns all open/in-progress handoffs for the admin panel."""
    handoffs = (
        db.query(AgentHandoff)
        .filter(AgentHandoff.status.in_(["open", "in_progress"]))
        .order_by(AgentHandoff.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": str(h.id),
            "session_id": str(h.session_id) if h.session_id else None,
            "user_id": str(h.user_id) if h.user_id else None,
            "from_agent_name": h.from_agent_name,
            "reason": h.reason,
            "summary": h.summary,
            "status": h.status.value if h.status else "open",
            "escalation_level": h.escalation_level,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in handoffs
    ]
