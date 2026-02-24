# app/ai/handoff.py
from app.ai.state import AgentState
from langchain_core.messages import AIMessage

def handoff_node(state: AgentState):
    """Halts AI processing and flags for human intervention."""
    # This pending_human_input flag tells the router to stop sending to AI
    return {
        "pending_human_input": True, 
        "messages": [AIMessage(content="I am having trouble processing that. I've connected you with our human support team who will reply shortly.")]
    }