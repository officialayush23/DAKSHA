# app/api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import re
import json
from typing import Optional, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models.models import User
from sqlalchemy.orm import Session

from app.ai.graph import agent_workflow
from app.ai.context_loader import load_context
from app.services.preference_service import refresh_user_preference_summary
from app.services.chat_session_service import (
    create_session,
    get_session,
    list_sessions,
    append_message,
    get_messages,
    get_context_for_llm,
    generate_session_name,
    set_session_name,
    update_rolling_summary,
)

router = APIRouter(prefix="/chat", tags=["Agentic Chat"])

# ── Schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # None = start a new session
    channel: str = "web"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    session_name: Optional[str] = None
    current_agent: Optional[str] = "UnifiedAgent"
    human_takeover: bool = False
    ui_data: Optional[Dict[str, Any]] = None

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
    message: str

# ── One-time checkpointer setup flag ─────────────────────────────────────────
_checkpointer_setup_done = False

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/sessions/new", response_model=NewSessionResponse)
def new_chat_session(
    channel: str = "web",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session (called when user clicks 'New Chat')."""
    session = create_session(db, str(current_user.id), channel)
    return NewSessionResponse(session_id=str(session.id))


@router.get("/sessions", response_model=List[SessionListItem])
def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all chat sessions for the user (newest first)."""
    sessions = list_sessions(db, str(current_user.id))
    return [
        SessionListItem(
            session_id=str(s.id),
            name=s.name,
            channel=s.channel,
            last_message_at=s.last_message_at.isoformat() if s.last_message_at else None,
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageItem])
def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Load the message history for a specific chat session."""
    chat_session = get_session(db, session_id, str(current_user.id))
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = get_messages(db, session_id)
    return [
        ChatMessageItem(
            role=m.role,
            content=m.content,
            ui_data=m.ui_data,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in msgs
        if m.role in ("user", "assistant")   # skip raw tool messages
    ]


@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    global _checkpointer_setup_done
    try:
        user_id_str = str(current_user.id)

        # ── 1. Resolve or create session ──────────────────────────────────────
        if request.session_id:
            chat_session = get_session(db, request.session_id, user_id_str)
            if not chat_session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            chat_session = create_session(db, user_id_str, request.channel)

        session_id_str = str(chat_session.id)

        # ── 2. Persist user message ───────────────────────────────────────────
        append_message(db, session_id_str, "user", request.message)

        # ── 3. Build context ──────────────────────────────────────────────────
        context = load_context(db, user_id_str, session_id_str)
        ctx_data = get_context_for_llm(db, session_id_str)

        # Build summary context string for the agent
        summary_context = context.get("user_summary", "")
        if ctx_data.get("summary"):
            summary_context += f"\n\nConversation summary so far:\n{ctx_data['summary']}"

        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": user_id_str,
            "session_id": session_id_str,
            "channel": request.channel,
            "order_mode": "online",
            "user_summary": summary_context,
            "conversation_summary": ctx_data.get("summary"),
        }

        config = {"configurable": {"thread_id": session_id_str}}

        # ── 4. Run LangGraph ──────────────────────────────────────────────────
        lg_url = settings.LANGGRAPH_DB_URL or settings.DATABASE_URL
        async with AsyncPostgresSaver.from_conn_string(lg_url, pipeline=False) as checkpointer:
            if not _checkpointer_setup_done:
                await checkpointer.setup()
                _checkpointer_setup_done = True

            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            final_state = await app_graph.ainvoke(input_state, config)

        # ── 5. Extract response ───────────────────────────────────────────────
        last_msg = final_state["messages"][-1]
        is_human_takeover = final_state.get("pending_human_input", False)
        active_agent = final_state.get("current_agent", "UnifiedAgent")

        response_text = (
            last_msg.content if isinstance(last_msg, AIMessage)
            else "I'm processing your request..."
        )

        # Extract UI JSON payload
        ui_data = None
        match = re.search(r'<UI_DATA>(.*?)</UI_DATA>', response_text, re.DOTALL)
        if match:
            try:
                ui_data = json.loads(match.group(1))
                response_text = response_text.replace(match.group(0), "").strip()
            except Exception as parse_error:
                print(f"⚠️ JSON Parse Error: {parse_error}")

        # ── 6. Persist assistant message (with ui_data so history re-renders cards)
        append_message(db, session_id_str, "assistant", response_text, ui_data=ui_data)

        # ── 7. Background: name session after first message, refresh taste profile
        is_first_message = chat_session.name is None
        if is_first_message:
            background_tasks.add_task(
                _name_session_async, db, session_id_str, request.message
            )

        background_tasks.add_task(
            refresh_user_preference_summary,
            user_id_str,
            session_id_str,
        )

        print(f"\n{'='*50}\n🤖 AGENT: {active_agent}\n💬 {response_text[:200]}\n{'='*50}\n")

        return ChatResponse(
            response=response_text,
            session_id=session_id_str,
            session_name=chat_session.name,
            current_agent=active_agent,
            human_takeover=is_human_takeover,
            ui_data=ui_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[CHAT ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _name_session_async(db: Session, session_id: str, first_message: str):
    """Background task: generate and save AI session name."""
    try:
        name = generate_session_name(first_message)
        set_session_name(db, session_id, name)
    except Exception as e:
        print(f"[SESSION NAMING ERROR]: {e}")


@router.post("/admin-reply")
async def admin_chat_resume(
    request: AdminReplyRequest,
    current_admin: User = Depends(get_current_user),
):
    """Injects admin message into the thread and resets human handoff."""
    config = {"configurable": {"thread_id": request.session_id}}
    try:
        lg_url = settings.LANGGRAPH_DB_URL or settings.DATABASE_URL
        async with AsyncPostgresSaver.from_conn_string(lg_url, pipeline=False) as checkpointer:
            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            state_update = {
                "messages": [AIMessage(content=f"👨‍💻 [Support Admin]: {request.message}")],
                "pending_human_input": False,
                "failure_count": 0,
            }
            await app_graph.ainvoke(state_update, config)
        return {"status": "Message injected to thread successfully."}
    except Exception as e:
        print(f"[ADMIN REPLY ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))
