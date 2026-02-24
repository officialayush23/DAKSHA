# app/ai/state.py
from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Context
    user_id: str
    session_id: str
    channel: str
    
    # Memory
    user_summary: Optional[str]
    conversation_summary: Optional[str]
    context_data: Dict[str, Any]
    
    # Routing & Handoff
    current_agent: Optional[str]
    failure_count: int
    pending_human_input: bool