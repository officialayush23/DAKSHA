# app/api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import re
import json
from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models.models import User
from sqlalchemy.orm import Session

from app.ai.graph import agent_workflow
from app.ai.context_loader import load_context
from app.services.preference_service import refresh_user_preference_summary

router = APIRouter(prefix="/chat", tags=["Agentic Chat"])

# ---------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str
    channel: str = "web"

class ChatResponse(BaseModel):
    response: str
    current_agent: Optional[str] = "UnifiedAgent"
    human_takeover: bool = False
    ui_data: Optional[Dict[str, Any]] = None

class AdminReplyRequest(BaseModel):
    session_id: str
    message: str

# ---------------------------------------------------------
# One-time checkpointer setup flag
# setup() creates LangGraph checkpoint tables — only needs to run once per process
# ---------------------------------------------------------
_checkpointer_setup_done = False


async def _get_checkpointer(lg_url: str) -> AsyncPostgresSaver:
    """
    Build an AsyncPostgresSaver with:
      • pipeline=False  — avoids psycopg AsyncPipeline SSL corruption on Supabase
      • setup() called once per process lifetime
    """
    global _checkpointer_setup_done
    # pipeline=False: use simple request/response mode instead of psycopg pipeline.
    # Supabase's SSL layer drops the pipeline connection intermittently, causing
    # "AsyncPipeline [BAD] / SSL error: bad length" errors.
    saver = AsyncPostgresSaver.from_conn_string(lg_url, pipeline=False)
    return saver


# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------

@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    global _checkpointer_setup_done
    try:
        user_id_str = str(current_user.id)

        # Load User & Conversation Context
        context = load_context(db, user_id_str, request.session_id)

        # Build State
        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": user_id_str,
            "session_id": request.session_id,
            "channel": request.channel,
            "user_summary": context.get("user_summary"),
            "conversation_summary": context.get("conversation_summary"),
        }

        config = {"configurable": {"thread_id": request.session_id}}

        # Run LangGraph with Postgres Checkpointer
        # Session-pooler URL (port 5432) — supports prepared statements
        # pipeline=False — avoids psycopg AsyncPipeline SSL drops on Supabase
        lg_url = settings.LANGGRAPH_DB_URL or settings.DATABASE_URL
        async with AsyncPostgresSaver.from_conn_string(lg_url, pipeline=False) as checkpointer:
            # setup() is idempotent but runs DDL — skip after first call
            if not _checkpointer_setup_done:
                await checkpointer.setup()
                _checkpointer_setup_done = True

            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            final_state = await app_graph.ainvoke(input_state, config)

        # Extract final LLM message
        last_msg = final_state["messages"][-1]
        is_human_takeover = final_state.get("pending_human_input", False)
        active_agent = final_state.get("current_agent", "UnifiedAgent")

        response_text = (
            last_msg.content if isinstance(last_msg, AIMessage)
            else "I'm processing your request..."
        )

        # Extract UI JSON payload from <UI_DATA>...</UI_DATA> tags
        ui_data = None
        match = re.search(r'<UI_DATA>(.*?)</UI_DATA>', response_text, re.DOTALL)
        if match:
            try:
                ui_data = json.loads(match.group(1))
                response_text = response_text.replace(match.group(0), "").strip()
            except Exception as parse_error:
                print(f"⚠️ JSON Parse Error: {parse_error}")

        print("\n" + "="*50)
        print(f"🤖 AGENT     : {active_agent}")
        print(f"💬 TEXT ONLY : {response_text}")
        print(f"📦 UI DATA   : {json.dumps(ui_data, indent=2) if ui_data else 'NONE'}")
        print("="*50 + "\n")

        # Background: refresh user taste profile after every turn
        background_tasks.add_task(
            refresh_user_preference_summary,
            user_id_str,
            request.session_id,
        )

        return ChatResponse(
            response=response_text,
            current_agent=active_agent,
            human_takeover=is_human_takeover,
            ui_data=ui_data,
        )

    except Exception as e:
        print(f"[CHAT ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin-reply")
async def admin_chat_resume(
    request: AdminReplyRequest,
    current_admin: User = Depends(get_current_user)
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
