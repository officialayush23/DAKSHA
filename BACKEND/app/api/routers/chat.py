# app/api/routers/chat.py
"""
Conversational API for every channel (web/PWA, app, kiosk, Telegram).

POST /chat/                         one message → orchestration graph → reply + cards + plan/trace
POST /chat/approvals/{id}           customer confirms or declines a paused action (e.g. "place ₹2,499 order?")
GET  /chat/sessions, /chat/sessions/{id}/messages
POST /chat/upload-image             image for visual search
POST /chat/admin-reply              staff message into a handed-off conversation (admin only)
GET  /chat/graph                    Mermaid source of the live LangGraph
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_current_user, get_db
from app.models.models import User
from app.services.chat_session_service import (
    append_message, create_session, generate_session_name, get_messages, get_session, list_sessions,
    set_session_name,
)
from app.services.preference_service import refresh_user_preference_summary

router = APIRouter(prefix="/chat", tags=["Agentic Chat"])

CHANNELS = {"web", "pwa", "app", "kiosk", "telegram"}


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=4000)
    session_id: Optional[str] = None   # None = start a new session
    channel: str = "web"
    image_url: Optional[str] = None
    store_id: Optional[str] = None      # kiosk / in-store context


class ChatResponse(BaseModel):
    response: str
    session_id: str
    session_name: Optional[str] = None
    current_agent: Optional[str] = None
    agents: List[str] = []
    human_takeover: bool = False
    ui_data: Optional[Dict[str, Any]] = None
    plan: List[Dict[str, Any]] = []
    trace: List[Dict[str, Any]] = []
    approval: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None


class ApprovalDecision(BaseModel):
    approved: bool
    note: Optional[str] = Field(default=None, max_length=500)


class NewSessionResponse(BaseModel):
    session_id: str


class SessionListItem(BaseModel):
    session_id: str
    name: Optional[str]
    channel: str
    last_message_at: Optional[str]
    updated_at: str


class ChatMessageItem(BaseModel):
    role: str
    content: str
    ui_data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class AdminReplyRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=4000)


# ── helpers ───────────────────────────────────────────────────────────────────

def _channel(c: str, user_payload_channel: Optional[str] = None) -> str:
    c = (c or "web").lower()
    return c if c in CHANNELS else "web"


def _store_for(user: User, req: ChatRequest) -> Optional[str]:
    # a kiosk token pins the store; web users may pass one (e.g. picked pickup store)
    pinned = getattr(user, "_token_store_id", None)
    return pinned or req.store_id


def _name_session_async(session_id: str, first_message: str):
    from app.core.database import SessionLocal
    try:
        name = generate_session_name(first_message)
        with SessionLocal() as db:
            set_session_name(db, session_id, name)
    except Exception as e:
        print(f"[SESSION NAMING ERROR]: {e}")


def _open_handoff(db: Session, chat_session_id: str):
    return db.execute(text("""SELECT id FROM agent_handoffs WHERE chat_session_id = :s
                              AND status IN ('open','in_progress') ORDER BY created_at DESC LIMIT 1"""),
                      {"s": chat_session_id}).first()


def _to_response(out: Dict[str, Any], session_id: str, name: Optional[str]) -> ChatResponse:
    agents = out.get("agents") or []
    ui = out.get("ui")
    if out.get("approval") and out["approval"].get("approver") == "customer":
        ui = {"type": "approval", "approval": out["approval"], **({"card": ui} if ui else {})}
    return ChatResponse(
        response=out.get("reply") or "",
        session_id=session_id,
        session_name=name,
        current_agent=agents[-1] if agents else "orchestrator",
        agents=agents,
        human_takeover=bool(out.get("handoff")),
        ui_data=ui,
        plan=out.get("plan") or [],
        trace=out.get("trace") or [],
        approval=out.get("approval"),
        latency_ms=out.get("latency_ms"),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/upload-image")
async def upload_chat_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    from app.services.storage_service import upload_chat_image as _upload
    allowed = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/heic"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Unsupported image type")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be under 10 MB")
    try:
        return {"url": _upload(data, file.content_type, file.filename or "image.jpg")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.post("/sessions/new", response_model=NewSessionResponse)
def new_chat_session(channel: str = "web", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = create_session(db, str(current_user.id), _channel(channel))
    return NewSessionResponse(session_id=str(session.id))


@router.get("/sessions", response_model=List[SessionListItem])
def get_chat_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [SessionListItem(session_id=str(s.id), name=s.name, channel=s.channel,
                            last_message_at=s.last_message_at.isoformat() if s.last_message_at else None,
                            updated_at=s.updated_at.isoformat())
            for s in list_sessions(db, str(current_user.id))]


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageItem])
def get_session_messages(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_session(db, session_id, str(current_user.id)):
        raise HTTPException(status_code=404, detail="Session not found")
    return [ChatMessageItem(role=m.role, content=m.content, ui_data=m.ui_data,
                            created_at=m.created_at.isoformat() if m.created_at else None)
            for m in get_messages(db, session_id) if m.role in ("user", "assistant", "staff")]


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, background_tasks: BackgroundTasks,
                          current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.agentic.runtime import run_turn

    if not (request.message or "").strip() and not request.image_url:
        raise HTTPException(status_code=400, detail="Empty message")
    uid = str(current_user.id)
    channel = getattr(current_user, "_token_channel", None) or _channel(request.channel)

    if request.session_id:
        chat_session = get_session(db, request.session_id, uid)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        chat_session = create_session(db, uid, channel)
    sid = str(chat_session.id)
    append_message(db, sid, "user", request.message or "(image)")

    # A human is handling this thread: relay instead of answering
    h = _open_handoff(db, sid)
    if h:
        try:
            from app.api.routers.websocket_handoff import relay_customer_message
            await relay_customer_message(db, str(h.id), sid, request.message)
        except Exception as e:
            print(f"[HANDOFF RELAY] {e}")
        return ChatResponse(response="Your message was passed to our team member, who will reply here.",
                            session_id=sid, session_name=chat_session.name, current_agent="human", human_takeover=True)

    try:
        out = await run_turn(thread_id=sid, user_id=uid, session_id=sid, message=request.message or "",
                             channel=channel, store_id=_store_for(current_user, request), image_url=request.image_url)
    except Exception as e:
        print(f"[CHAT ERROR]: {e}")
        raise HTTPException(status_code=503, detail="The assistant is temporarily unavailable. Please try again.")

    resp = _to_response(out, sid, chat_session.name)
    stored_ui = dict(resp.ui_data or {})
    stored_ui["_agentic"] = {"agents": resp.agents, "plan": resp.plan, "approval": resp.approval, "latency_ms": resp.latency_ms}
    append_message(db, sid, "assistant", resp.response, ui_data=stored_ui)

    if chat_session.name is None:
        background_tasks.add_task(_name_session_async, sid, request.message or "Image search")
    background_tasks.add_task(refresh_user_preference_summary, uid, sid)
    return resp


@router.post("/approvals/{approval_id}", response_model=ChatResponse)
async def decide_approval(approval_id: str, payload: ApprovalDecision,
                          current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The customer confirms or declines an action the agents paused on."""
    from app.agentic.runtime import resume
    row = db.execute(text("SELECT * FROM agent_approvals WHERE id = :id"), {"id": approval_id}).mappings().first()
    if not row or str(row["user_id"]) != str(current_user.id) or row["approver_role"] != "customer":
        raise HTTPException(status_code=404, detail="Nothing to confirm")
    if row["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Already {row['status']}")
    try:
        out = await resume(thread_id=row["thread_id"], approval_id=approval_id, approved=payload.approved,
                           by=str(current_user.id), note=payload.note)
    except LookupError as e:
        raise HTTPException(status_code=409, detail=str(e))
    sid = row["thread_id"]
    resp = _to_response(out, sid, None)
    stored_ui = dict(resp.ui_data or {})
    stored_ui["_agentic"] = {"agents": resp.agents, "plan": resp.plan, "approval": resp.approval}
    append_message(db, sid, "user", "✅ Confirmed" if payload.approved else "✖ Declined")
    append_message(db, sid, "assistant", resp.response, ui_data=stored_ui)
    return resp


@router.post("/admin-reply")
async def admin_chat_reply(request: AdminReplyRequest, current_admin: User = Depends(get_current_admin),
                           db: Session = Depends(get_db)):
    """Staff message into a handed-off conversation (admin role required)."""
    h = _open_handoff(db, request.session_id)
    if not h:
        raise HTTPException(status_code=404, detail="No open handoff for this conversation")
    from app.api.routers.websocket_handoff import relay_admin_message
    await relay_admin_message(db, str(h.id), request.session_id, request.message, str(current_admin.id))
    return {"status": "sent"}


@router.get("/graph")
def orchestration_graph(current_user: User = Depends(get_current_user)):
    from app.agentic.runtime import get_engine
    eng = get_engine()
    g = eng.build().compile().get_graph()
    return {"mermaid": g.draw_mermaid(), "agents": [a.name for a in eng.pack.agents],
            "tools": {a.name: a.tools for a in eng.pack.agents}}
