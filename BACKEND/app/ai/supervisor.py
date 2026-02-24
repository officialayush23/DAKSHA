# app/ai/supervisor.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.routing import RouteSchema
from app.ai.state import AgentState

def supervisor_node(state: AgentState):
    """Analyzes the conversation and routes to the correct worker."""
    
    # 1. Hard Handoff Check
    if state.get("failure_count", 0) >= 3 or state.get("pending_human_input"):
        return {"current_agent": "Handoff"}

    # 2. Routing LLM
    llm = get_llm().with_structured_output(RouteSchema)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the Sales Orchestrator. Route the user's request.
        User Context: {user_summary}
        
        Choose FINISH if you can answer a simple greeting yourself.
        Otherwise, choose the appropriate Agent."""),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    chain = prompt | llm
    decision = chain.invoke({
        "messages": state["messages"],
        "user_summary": state.get("user_summary", "")
    })
    
    return {"current_agent": decision.next_agent}