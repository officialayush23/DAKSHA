# app/ai/supervisor.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage  # <-- ADDED IMPORT
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
        ("system", """You are the lead Sales Agent for our online store. 
        User Context: {user_summary}
        
        Choose FINISH if the user says hello, asks general questions, or if the conversation is over.
        If you choose FINISH, you MUST populate the 'response' field with a friendly, helpful reply.
        
        If they want to find products, manage their cart, get support, or use loyalty points, 
        choose the appropriate Agent and leave 'response' empty."""),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    chain = prompt | llm
    decision = chain.invoke({
        "messages": state["messages"],
        "user_summary": state.get("user_summary", "No prior context.")
    })
    
    # 3. Build the state update
    updates = {"current_agent": decision.next_agent}
    
    # 4. If finishing, append the LLM's conversational response
    if decision.next_agent == "FINISH" and decision.response:
        updates["messages"] = [AIMessage(content=decision.response)]
    
    # <-- FIXED: Return the 'updates' dict, not just the agent string
    return updates