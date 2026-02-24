# app/api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models.models import User
from sqlalchemy.orm import Session

# Import your AI logic
from app.ai.graph import agent_workflow
from app.ai.context_loader import load_context

router = APIRouter(prefix="/chat", tags=["Agentic Chat"])

# ---------------------------------------------------------
# 1. SETUP POSTGRES CONNECTION POOL FOR LANGGRAPH MEMORY
# ---------------------------------------------------------
# This ensures the agent remembers the user across Web & Kiosk channels.
pool = AsyncConnectionPool(
    conninfo=settings.DATABASE_URL,
    max_size=10,
    kwargs={"autocommit": True, "prepare_threshold": 0},
)

# ---------------------------------------------------------
# 2. SCHEMAS
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
# 3. ENDPOINTS
# ---------------------------------------------------------

@router.post("/", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        user_id_str = str(current_user.id)
        
        # 1. Load dynamic user & conversation context
        context = load_context(db, user_id_str, request.session_id)
        
        # 2. Build the input state
        # Because we use `add_messages` in AgentState, LangGraph will automatically
        # append this new HumanMessage to the existing thread history in the database.
        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": user_id_str,
            "session_id": request.session_id,
            "channel": request.channel,
            "user_summary": context.get("user_summary"),
            "conversation_summary": context.get("conversation_summary"),
        }

        # 3. Configure thread (session persistence)
        config = {"configurable": {"thread_id": request.session_id}}

        # 4. Invoke the Graph with Postgres Checkpointer
        async with AsyncPostgresSaver(pool) as checkpointer:
            # Note: You usually run `await checkpointer.setup()` once on app startup, 
            # but we can ensure it's ready here if needed.
            await checkpointer.setup() 
            
            app_graph = agent_workflow.compile(checkpointer=checkpointer)
            
            # Run the multi-agent graph
            final_state = await app_graph.ainvoke(input_state, config)

        # 5. Extract final response to send to the frontend
        last_msg = final_state["messages"][-1]
        is_human_takeover = final_state.get("pending_human_input", False)
        active_agent = final_state.get("current_agent", "Supervisor")
        
        # Ensure we return a string even if the last message is a Tool call anomaly
        response_text = last_msg.content if isinstance(last_msg, AIMessage) else "I'm processing your request..."

        return ChatResponse(
            response=response_text,
            current_agent=active_agent,
            human_takeover=is_human_takeover
        )

    except Exception as e:
        print(f"[CHAT ERROR]: {e}")
        raise HTTPException(status_code=500, detail="The agent encountered an error processing your request.")

