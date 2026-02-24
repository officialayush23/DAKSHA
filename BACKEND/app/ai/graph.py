# app/ai/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage

from app.ai.state import AgentState
from app.ai.llm import get_llm

# --- IMPORT ALL TOOLS ---
from app.ai.tools.recommendation_tools import recommend_products, search_for_items, find_similar_by_image, get_trending_products
from app.ai.tools.checkout_tools import (
    view_cart, add_to_cart, update_cart_quantity, remove_from_cart,
    start_delivery_checkout, start_pickup_checkout, finalize_payment
)
from app.ai.tools.loyalty_tools import (
    get_loyalty_balance, get_checkout_coupons, apply_discount_code, 
    generate_personalized_offer, list_available_offers
)
from app.ai.tools.user_tools import get_user_profile, get_user_saved_addresses
from app.ai.tools.inventory_tools import check_item_stock, find_nearest_pickup_stores, agent_reschedule_delivery

# Import the new expansive support tools
from app.ai.tools.support_tools import (
    process_return, view_returns, cancel_return_request_tool,
    process_exchange, view_exchanges,
    request_order_cancel,
    create_complaint, view_complaints,
    request_human_handoff
)

# 1. Pool all tools into one master list
all_tools = [
    recommend_products, search_for_items, find_similar_by_image, get_trending_products,
    view_cart, add_to_cart, update_cart_quantity, remove_from_cart,
    start_delivery_checkout, start_pickup_checkout, finalize_payment,
    get_loyalty_balance, get_checkout_coupons, apply_discount_code, generate_personalized_offer, list_available_offers,
    get_user_profile, get_user_saved_addresses,
    check_item_stock, find_nearest_pickup_stores, agent_reschedule_delivery,
    process_return, view_returns, cancel_return_request_tool,
    process_exchange, view_exchanges,
    request_order_cancel,
    create_complaint, view_complaints,
    request_human_handoff
]

# 2. Bind to LLM
llm = get_llm()
llm_with_tools = llm.bind_tools(all_tools)

# 3. Master Prompt
MASTER_PROMPT = """You are the OmniChannel AI Assistant. You have tools for Cart, Checkout, Support, Catalog, Loyalty, and Profiles.

CRITICAL RULES:
1. Detect the user's intent. Call the EXACT ONE tool required. Do NOT overthink.
2. If the user wants a discount, proactively call `generate_personalized_offer`.
3. If the user is angry, confused, or explicitly asks for a human, call `request_human_handoff` immediately.
4. Once you receive the tool's result, immediately summarize it for the user and stop.
5. If a tool returns JSON data, you MUST wrap it in <UI_DATA> [json here] </UI_DATA> tags in your final text response.

Current User ID: {user_id}
Current Session ID: {session_id}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", MASTER_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain_with_tools = prompt | llm_with_tools
chain_text_only = prompt | llm  # NO tools attached for the anti-loop

# 4. The Single Unified Node with Force-Text
def unified_agent_node(state: AgentState):
    messages = state["messages"]
    
    # ANTI-LOOP: If the last message was a tool result, force a text reply.
    if len(messages) > 0 and isinstance(messages[-1], ToolMessage):
        response = chain_text_only.invoke({
            "messages": messages,
            "user_id": state["user_id"],
            "session_id": state["session_id"]
        })
    else:
        response = chain_with_tools.invoke({
            "messages": messages,
            "user_id": state["user_id"],
            "session_id": state["session_id"]
        })
        
    return {"messages": [response], "current_agent": "UnifiedAgent"}

def route_tools(state: AgentState):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return END

# 5. Build Graph
def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("agent", unified_agent_node)
    builder.add_node("tools", ToolNode(all_tools))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_tools)
    builder.add_edge("tools", "agent")

    return builder

agent_workflow = build_graph()