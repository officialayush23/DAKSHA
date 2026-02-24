# app/api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# REMOVE the AsyncConnectionPool import from psycopg_pool

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
    current_agent: Optional[str] = "SalesSupervisor"
    human_takeover: bool = False

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
        
        context = load_context(db, user_id_str, request.session_id)
        
        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": user_id_str,
            "session_id": request.session_id,
            "channel": request.channel,
            "user_summary": context.get("user_summary"),
            "conversation_summary": context.get("conversation_summary"),
        }

        config = {"configurable": {"thread_id": request.session_id}}

        # 👇 FIXED: Use .from_conn_string() which perfectly supports `async with`
        async with AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
            
            # Setup the tables if they don't exist yet
            await checkpointer.setup() 
            
            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            
            final_state = await app_graph.ainvoke(input_state, config)

        last_msg = final_state["messages"][-1]
        is_human_takeover = final_state.get("pending_human_input", False)
        active_agent = final_state.get("current_agent", "Supervisor")
        
        response_text = last_msg.content if isinstance(last_msg, AIMessage) else "I'm processing your request..."

        return ChatResponse(
            response=response_text,
            current_agent=active_agent,
            human_takeover=is_human_takeover
        )

    except Exception as e:
        print(f"[CHAT ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))