# app/api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
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
    ui_data: Optional[Dict[str, Any]] = None  # ⬅️ FOR FRONTEND RENDERING

class AdminReplyRequest(BaseModel):
    session_id: str
    message: str

# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------

@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
            await checkpointer.setup() 
            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            
            # This triggers the agent -> tools -> agent flow
            final_state = await app_graph.ainvoke(input_state, config)

        # Extract final LLM message
        last_msg = final_state["messages"][-1]
        is_human_takeover = final_state.get("pending_human_input", False)
        active_agent = final_state.get("current_agent", "UnifiedAgent")
        
        response_text = last_msg.content if isinstance(last_msg, AIMessage) else "I'm processing your request..."
        
        # 🟢 MAGIC TRICK: Extract UI JSON for Frontend
        ui_data = None
        match = re.search(r'<UI_DATA>(.*?)</UI_DATA>', response_text, re.DOTALL)
        if match:
            try:
                # Parse the JSON string hidden in the text
                ui_data = json.loads(match.group(1))
                # Remove the raw JSON payload from the conversational text so the user doesn't see it
                response_text = response_text.replace(match.group(0), "").strip()
            except Exception as parse_error:
                print(f"⚠️ JSON Parse Error: {parse_error}")

        # 🚀 DEBUG PRINTS - You will see this in your Uvicorn terminal!
        print("\n" + "="*50)
        print(f"🤖 AGENT     : {active_agent}")
        print(f"💬 TEXT ONLY : {response_text}")
        print(f"📦 UI DATA   : {json.dumps(ui_data, indent=2) if ui_data else 'NONE'}")
        print("="*50 + "\n")

        return ChatResponse(
            response=response_text,
            current_agent=active_agent,
            human_takeover=is_human_takeover,
            ui_data=ui_data
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
        async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            
            state_update = {
                "messages": [AIMessage(content=f"👨‍💻 [Support Admin]: {request.message}")],
                "pending_human_input": False, 
                "failure_count": 0
            }
            
            await app_graph.ainvoke(state_update, config)
            
        return {"status": "Message injected to thread successfully."}
    except Exception as e:
        print(f"[ADMIN REPLY ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))