import operator
from typing import Annotated, List, TypedDict, Union, Literal
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from app.services.ai_service import AIService
from app.agents.tools import (
    search_products_tool, get_personalized_recommendations_tool, get_active_campaigns_tool,
    check_stock_tool, find_nearest_store_tool,
    add_to_cart_tool, checkout_tool,
    check_loyalty_status_tool,
    create_ticket_tool, track_order_tool
)

# 1. Define State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    channel: str
    next: str

llm = AIService.get_llm()

# --- 2. Robust Worker Creation (No 'create_react_agent') ---
# We manually define how a worker behaves to avoid library version issues.

def create_worker_node(tools, system_prompt):
    """
    Manually creates a worker node function.
    This replaces create_react_agent to be version-proof.
    """
    # Bind tools to the LLM
    worker_llm = llm.bind_tools(tools)
    
    # Create the ToolNode for execution
    tool_node = ToolNode(tools)
    
    # The actual node logic
    def worker_node(state: AgentState):
        msgs = state["messages"]
        # Prepend the System Prompt manually
        sys_msg = SystemMessage(content=system_prompt)
        # Filter out previous system messages to keep context clean
        filtered_msgs = [m for m in msgs if not isinstance(m, SystemMessage)]
        
        response = worker_llm.invoke([sys_msg] + filtered_msgs)
        return {"messages": [response]}
        
    return worker_node, tool_node

# --- Define Workers ---

# Recommendation Agent
rec_tools = [search_products_tool, get_personalized_recommendations_tool, get_active_campaigns_tool]
rec_node, rec_tool_node = create_worker_node(
    rec_tools,
    "You are the Recommendation Agent. Suggest products based on history/trends. Use tools to find items."
)

# Inventory Agent
inv_tools = [check_stock_tool, find_nearest_store_tool]
inv_node, inv_tool_node = create_worker_node(
    inv_tools,
    "You are the Inventory Agent. Check stock levels and find stores."
)

# Payment Agent
pay_tools = [add_to_cart_tool, checkout_tool]
pay_node, pay_tool_node = create_worker_node(
    pay_tools,
    "You are the Payment Agent. Handle Cart operations and Checkout."
)

# Loyalty Agent
loy_tools = [check_loyalty_status_tool]
loy_node, loy_tool_node = create_worker_node(
    loy_tools,
    "You are the Loyalty Agent. Explain points, rewards, and coupons."
)

# Support Agent
sup_tools = [create_ticket_tool, track_order_tool]
sup_node, sup_tool_node = create_worker_node(
    sup_tools,
    "You are the Support Agent. Handle returns and complaints."
)

# --- 3. The Supervisor (Sales Agent) ---

class RouteResponse(BaseModel):
    next: Literal[
        "RecommendationAgent", 
        "InventoryAgent", 
        "PaymentAgent", 
        "LoyaltyAgent", 
        "SupportAgent", 
        "FINISH"
    ]

supervisor_system_prompt = (
    "You are Daksha, the Head Sales Associate. "
    "Route the user to the correct specialist based on their intent. "
    " - RecommendationAgent: Product discovery, styling. "
    " - InventoryAgent: Stock checks, store location. "
    " - PaymentAgent: Buy, Cart, Checkout. "
    " - LoyaltyAgent: Points, Offers. "
    " - SupportAgent: Orders, Returns, Complaints. "
    " - FINISH: If the user says hello/thanks or the task is done."
)

prompt = ChatPromptTemplate.from_messages([
    ("system", supervisor_system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    ("system", "Select the next agent: RecommendationAgent, InventoryAgent, PaymentAgent, LoyaltyAgent, SupportAgent, FINISH.")
])

def supervisor_node(state: AgentState):
    chain = prompt | llm.with_structured_output(RouteResponse)
    result = chain.invoke(state)
    return {"next": result.next}

# --- 4. Build the Graph ---

workflow = StateGraph(AgentState)

# Add Agent Nodes
workflow.add_node("SalesAgent", supervisor_node)
workflow.add_node("RecommendationAgent", rec_node)
workflow.add_node("InventoryAgent", inv_node)
workflow.add_node("PaymentAgent", pay_node)
workflow.add_node("LoyaltyAgent", loy_node)
workflow.add_node("SupportAgent", sup_node)

# Add Tool Execution Nodes (One per worker to keep scopes separate)
workflow.add_node("RecTools", rec_tool_node)
workflow.add_node("InvTools", inv_tool_node)
workflow.add_node("PayTools", pay_tool_node)
workflow.add_node("LoyTools", loy_tool_node)
workflow.add_node("SupTools", sup_tool_node)

# --- 5. Edges Logic ---

# Helper to decide: Tool vs Return to Supervisor
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "supervisor"

# Wiring: Supervisor -> Worker
workflow.add_conditional_edges(
    "SalesAgent",
    lambda x: x["next"],
    {
        "RecommendationAgent": "RecommendationAgent",
        "InventoryAgent": "InventoryAgent",
        "PaymentAgent": "PaymentAgent",
        "LoyaltyAgent": "LoyaltyAgent",
        "SupportAgent": "SupportAgent",
        "FINISH": END
    }
)

# Wiring: Worker -> Tools OR Supervisor
# Each worker checks: "Did I call a tool? If yes -> Go to My Tool Node. If no -> Go back to Supervisor"

# Recommendation Loop
workflow.add_conditional_edges("RecommendationAgent", should_continue, {"tools": "RecTools", "supervisor": "SalesAgent"})
workflow.add_edge("RecTools", "RecommendationAgent")

# Inventory Loop
workflow.add_conditional_edges("InventoryAgent", should_continue, {"tools": "InvTools", "supervisor": "SalesAgent"})
workflow.add_edge("InvTools", "InventoryAgent")

# Payment Loop
workflow.add_conditional_edges("PaymentAgent", should_continue, {"tools": "PayTools", "supervisor": "SalesAgent"})
workflow.add_edge("PayTools", "PaymentAgent")

# Loyalty Loop
workflow.add_conditional_edges("LoyaltyAgent", should_continue, {"tools": "LoyTools", "supervisor": "SalesAgent"})
workflow.add_edge("LoyTools", "LoyaltyAgent")

# Support Loop
workflow.add_conditional_edges("SupportAgent", should_continue, {"tools": "SupTools", "supervisor": "SalesAgent"})
workflow.add_edge("SupTools", "SupportAgent")

workflow.set_entry_point("SalesAgent")
daksha_graph = workflow.compile()

# --- 6. Runner Function ---
async def run_sales_agent(user_id: str, channel: str, channel_id: str, message: str):
    inputs = {
        "messages": [HumanMessage(content=message)],
        "user_id": user_id or "guest",
        "channel": channel
    }
    
    final_response = ""
    # Stream the graph to get the final response
    async for output in daksha_graph.astream(inputs):
        for key, value in output.items():
            if "messages" in value:
                final_response = value["messages"][-1].content
    
    return final_response