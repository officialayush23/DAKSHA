import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage

# Import the Graph we built in Part 2
from app.agents.graph import daksha_graph

# Import History Service (to save to DB)
#from app.services.chat_history_service import ChatHistoryService 

router = APIRouter()
logger = logging.getLogger("daksha.api")

# --- 1. Request Schema ---
class ChatRequest(BaseModel):
    user_id: str = Field(..., description="UUID of the user or 'guest'")
    session_id: str = Field(..., description="Unique session ID (or channel ID)")
    message: str = Field(..., description="User's text input")
    
    # Critical for "Nearby" inventory checks
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Contains lat, lng, device_type, kiosk_id"
    )

# --- 2. Response Schema ---
class ChatResponse(BaseModel):
    reply: str
    payload: Optional[Dict[str, Any]] = None # For UI Cards (Products, Orders)
    route_used: str

# --- 3. The Endpoint ---
@router.post("/message", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Main entry point for the Agentic AI.
    """
    try:
        user_id = payload.user_id
        session_id = payload.session_id
        user_msg = payload.message
        meta = payload.metadata or {}

        logger.info(f"📨 Msg from {user_id}: {user_msg[:50]}... | Meta: {meta}")

        # A. Save User Message to DB (Optional but recommended)
        # ChatHistoryService.save_message(session_id, "user", user_msg)

        # B. Load History (Optional)
        # For this "Free Tier" architecture, we keep history short (last 4 msgs) 
        # to save context window space.
        # history = ChatHistoryService.get_recent_messages(session_id, limit=4)
        history = [] # Placeholder if service missing

        # C. Prepare Graph Input
        initial_state = {
            "messages": history + [HumanMessage(content=user_msg)],
            "user_id": user_id,
            "session_id": session_id,
            "request_metadata": meta, # Pass lat/lng here
            "router_decision": {},
            "tool_output": None
        }

        # D. Run the Graph!
        final_state = await daksha_graph.ainvoke(initial_state)

        # E. Extract Result
        last_message = final_state["messages"][-1]
        reply_text = last_message.content
        
        # Extract internal state to send back as "Payload" for UI
        # (The UI uses this to render Carousels instead of just text)
        tool_data = final_state.get("tool_output")
        router_data = final_state.get("router_decision", {})
        route = router_data.get("route", "unknown")
        
        ui_payload = None
        
        # If the tool returned valid JSON (e.g., product list), send it as payload
        if route == "inventory" and tool_data:
            try:
                import json
                # If tool_output is a JSON string, parse it
                if isinstance(tool_data, str) and (tool_data.startswith("[") or tool_data.startswith("{")):
                     ui_payload = {"type": "products", "data": json.loads(tool_data)}
            except:
                pass # It was just text
                
        elif route == "support" and tool_data:
            try:
                import json
                if isinstance(tool_data, str) and (tool_data.startswith("[") or tool_data.startswith("{")):
                    ui_payload = {"type": "orders", "data": json.loads(tool_data)}
            except:
                pass

        # F. Save Bot Response to DB (Optional)
        # ChatHistoryService.save_message(session_id, "assistant", reply_text)

        logger.info(f"✅ Reply: {reply_text[:50]}... | Route: {route}")

        return ChatResponse(
            reply=reply_text,
            payload=ui_payload,
            route_used=route
        )

    except Exception as e:
        logger.error(f"🔥 API Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal AI Error")