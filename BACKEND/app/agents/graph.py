# app/agents/graph.py
# # app/agents/graph.py

# import operator
# from typing import Annotated, List, TypedDict, Literal

# from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolNode
# from pydantic import BaseModel

# from app.services.ai_service import AIService
# from app.database import supabase
# from app.agents.tools import (
#     # catalog / recommendation
#     search_products_tool,
#     get_personalized_recommendations_tool,
#     get_active_campaigns_tool,
#     # inventory / stores
#     check_stock_tool,
#     find_nearest_store_tool,
#     # cart & checkout
#     add_to_cart_tool,
#     checkout_tool,
#     # loyalty
#     check_loyalty_status_tool,
#     # support / orders
#     create_support_ticket_tool,
#     track_order_tool,
#     # fulfillment
#     schedule_fulfillment_tool,
#     get_fulfillment_status_tool,
#     # optional cross-cutting tools
#     send_notification_tool,
#     update_user_profile_tool,
# )

# from app.services.omni_session_service import OmniSessionService


# # ===============================
# # 1. STATE
# # ===============================

# class AgentState(TypedDict):
#     messages: Annotated[List[BaseMessage], operator.add]
#     user_id: str
#     channel: str
#     next: str
#     session_id: str | None


# llm = AIService.get_llm()


# # ===============================
# # 2. WORKER FACTORY
# # ===============================

# def create_worker_node(tools, system_prompt: str):
#     """
#     Create a worker node + its ToolNode.
#     Also logs each agent turn into agent_runs (best-effort).
#     """
#     worker_llm = llm.bind_tools(tools)
#     tool_node = ToolNode(tools)

#     def worker_node(state: AgentState):
#         msgs = state["messages"]

#         sys_msg = SystemMessage(content=system_prompt)
#         filtered_msgs = [m for m in msgs if not isinstance(m, SystemMessage)]

#         response = worker_llm.invoke([sys_msg] + filtered_msgs)

#         # --- Logging to agent_runs (fire-and-forget) ---
#         try:
#             last_input = filtered_msgs[-1].content if filtered_msgs else ""
#             out_text = getattr(response, "content", "")
#             supabase.table("agent_runs").insert(
#                 {
#                     "session_id": state.get("session_id"),
#                     "user_id": state.get("user_id"),
#                     "channel_type": state.get("channel"),
#                     "agent_name": system_prompt.split(".")[0][:50],
#                     "input_summary": str(last_input)[:500],
#                     "output_summary": str(out_text)[:500],
#                     "tool_calls": getattr(response, "tool_calls", None),
#                 }
#             ).execute()
#         except Exception:
#             # never block on logging
#             pass

#         return {"messages": [response]}

#     return worker_node, tool_node


# # ===============================
# # 3. AGENTS
# # ===============================

# # Recommendation
# rec_tools = [
#     search_products_tool,
#     get_personalized_recommendations_tool,
#     get_active_campaigns_tool,
# ]
# rec_node, rec_tool_node = create_worker_node(
#     rec_tools,
#     "RecommendationAgent. You suggest outfits and products based on history, style, and trends.",
# )

# # Inventory
# inv_tools = [
#     check_stock_tool,
#     find_nearest_store_tool,
# ]
# inv_node, inv_tool_node = create_worker_node(
#     inv_tools,
#     "InventoryAgent. You answer stock availability, sizes, nearest store, and in-store location.",
# )

# # Payment (cart + order creation)
# pay_tools = [
#     add_to_cart_tool,
#     checkout_tool,
# ]
# pay_node, pay_tool_node = create_worker_node(
#     pay_tools,
#     "PaymentAgent. You manage cart, compute totals & discounts via checkout, and prepare orders.",
# )

# # Loyalty
# loy_tools = [
#     check_loyalty_status_tool,
# ]
# loy_node, loy_tool_node = create_worker_node(
#     loy_tools,
#     "LoyaltyAgent. You explain loyalty points, tiers, and rewards.",
# )

# # Support
# sup_tools = [
#     create_support_ticket_tool,
#     track_order_tool,
# ]
# sup_node, sup_tool_node = create_worker_node(
#     sup_tools,
#     "SupportAgent. You handle complaints, returns, and order tracking.",
# )

# # Fulfillment (delivery / pickup / reservation)
# ful_tools = [
#     schedule_fulfillment_tool,
#     get_fulfillment_status_tool,
#     track_order_tool,
# ]
# ful_node, ful_tool_node = create_worker_node(
#     ful_tools,
#     "FulfillmentAgent. You schedule delivery/pickup/reservation and report fulfillment status.",
# )

# # You *could* make a separate EngagementAgent later that uses:
# # [update_user_profile_tool, send_notification_tool]
# # For now they are available as tools for future use, but not bound here.


# # ===============================
# # 4. SUPERVISOR (ROUTER)
# # ===============================

# class RouteResponse(BaseModel):
#     next: Literal[
#         "RecommendationAgent",
#         "InventoryAgent",
#         "PaymentAgent",
#         "LoyaltyAgent",
#         "SupportAgent",
#         "FulfillmentAgent",
#         "FINISH",
#     ]


# supervisor_system_prompt = (
#     "You are Daksha, the Head Sales Associate for a fashion retailer.\n"
#     "Decide which specialist agent should handle the user's latest message.\n\n"
#     "Use:\n"
#     "- RecommendationAgent: discovery, styling, 'what should I buy?'\n"
#     "- InventoryAgent: availability, sizes, nearest store, in-store navigation.\n"
#     "- PaymentAgent: cart changes, applying promo at checkout, issues before order is created.\n"
#     "- LoyaltyAgent: loyalty points, tiers, rewards, coupons explanation.\n"
#     "- SupportAgent: existing orders, complaints, returns, 'talk to human'.\n"
#     "- FulfillmentAgent: delivery options, pickup slots, reservations, order status after payment.\n"
#     "- FINISH: greetings, small talk, or when the task is clearly completed.\n"
# )

# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", supervisor_system_prompt),
#         MessagesPlaceholder(variable_name="messages"),
#         ("system", "Return the next agent to call."),
#     ]
# )


# def supervisor_node(state: AgentState):
#     chain = prompt | llm.with_structured_output(RouteResponse)
#     result = chain.invoke(state)
#     return {"next": result.next}


# # ===============================
# # 5. GRAPH WIRING
# # ===============================

# workflow = StateGraph(AgentState)

# workflow.add_node("SalesAgent", supervisor_node)

# workflow.add_node("RecommendationAgent", rec_node)
# workflow.add_node("InventoryAgent", inv_node)
# workflow.add_node("PaymentAgent", pay_node)
# workflow.add_node("LoyaltyAgent", loy_node)
# workflow.add_node("SupportAgent", sup_node)
# workflow.add_node("FulfillmentAgent", ful_node)

# workflow.add_node("RecTools", rec_tool_node)
# workflow.add_node("InvTools", inv_tool_node)
# workflow.add_node("PayTools", pay_tool_node)
# workflow.add_node("LoyTools", loy_tool_node)
# workflow.add_node("SupTools", sup_tool_node)
# workflow.add_node("FulTools", ful_tool_node)


# def should_continue(state: AgentState):
#     last = state["messages"][-1]
#     if getattr(last, "tool_calls", None):
#         return "tools"
#     return "supervisor"


# workflow.add_conditional_edges(
#     "SalesAgent",
#     lambda x: x["next"],
#     {
#         "RecommendationAgent": "RecommendationAgent",
#         "InventoryAgent": "InventoryAgent",
#         "PaymentAgent": "PaymentAgent",
#         "LoyaltyAgent": "LoyaltyAgent",
#         "SupportAgent": "SupportAgent",
#         "FulfillmentAgent": "FulfillmentAgent",
#         "FINISH": END,
#     },
# )

# # Rec loop
# workflow.add_conditional_edges(
#     "RecommendationAgent",
#     should_continue,
#     {"tools": "RecTools", "supervisor": "SalesAgent"},
# )
# workflow.add_edge("RecTools", "RecommendationAgent")

# # Inv loop
# workflow.add_conditional_edges(
#     "InventoryAgent",
#     should_continue,
#     {"tools": "InvTools", "supervisor": "SalesAgent"},
# )
# workflow.add_edge("InvTools", "InventoryAgent")

# # Pay loop
# workflow.add_conditional_edges(
#     "PaymentAgent",
#     should_continue,
#     {"tools": "PayTools", "supervisor": "SalesAgent"},
# )
# workflow.add_edge("PayTools", "PaymentAgent")

# # Loyalty loop
# workflow.add_conditional_edges(
#     "LoyaltyAgent",
#     should_continue,
#     {"tools": "LoyTools", "supervisor": "SalesAgent"},
# )
# workflow.add_edge("LoyTools", "LoyaltyAgent")

# # Support loop
# workflow.add_conditional_edges(
#     "SupportAgent",
#     should_continue,
#     {"tools": "SupTools", "supervisor": "SalesAgent"},
# )
# workflow.add_edge("SupTools", "SupportAgent")

# # Fulfillment loop
# workflow.add_conditional_edges(
#     "FulfillmentAgent",
#     should_continue,
#     {"tools": "FulTools", "supervisor": "SalesAgent"},
# )
# workflow.add_edge("FulTools", "FulfillmentAgent")

# workflow.set_entry_point("SalesAgent")
# daksha_graph = workflow.compile()


# # ===============================
# # 6. RUNNER
# # ===============================

# async def run_sales_agent(user_id: str | None, channel: str, channel_id: str, message: str):
#     """
#     Top-level orchestrator entry used by /channels/message.
#     Handles omni-session lookup and passes context into the graph.
#     """
#     omni = OmniSessionService.get_session(channel, channel_id)
#     session_id = omni.get("chat_session_id") if omni else None

#     inputs = {
#         "messages": [HumanMessage(content=message)],
#         "user_id": user_id or "guest",
#         "channel": channel,
#         "session_id": session_id,
#     }

#     final_response = ""
#     async for output in daksha_graph.astream(inputs):
#         for _, v in output.items():
#             if "messages" in v:
#                 final_response = v["messages"][-1].content

#     # upsert omni session – you can extend later to store a summary
#     OmniSessionService.upsert_session(
#         channel_type=channel,
#         channel_id=channel_id,
#         user_id=user_id,
#         chat_session_id=session_id,
#         active_cart_id=None,
#     )

#     return final_response




import operator
import json
import logging
from typing import Annotated, List, TypedDict, Any

from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Import Services
from app.services.catalog_service import CatalogService
from app.services.commerce_service import CommerceService
from app.services.ai_service import AIService
from app.services.router_service import RouterService
from app.database import supabase

logger = logging.getLogger("daksha.graph")

# --- 1. STATE DEFINITION ---
class AgentState(TypedDict):
    """
    The shared state passed between nodes.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    session_id: str
    
    # Metadata for the frontend (location, device)
    request_metadata: dict 
    
    # Internal flow data
    router_decision: dict 
    tool_output: Any 

# --- 2. NODES (The Agents) ---

async def router_node(state: AgentState):
    """
    Step 1: The Traffic Cop.
    Decides intent and fetches 'Always-On' context.
    """
    user_id = state.get("user_id", "guest")
    last_msg = state["messages"][-1].content
    
    # 1. Fetch Loyalty Context (SQL - Fast)
    context_str = await RouterService.get_loyalty_context(user_id)
    
    # 2. Classify Intent (Groq - Fast)
    decision = RouterService.classify_intent(last_msg, context_str)
    
    logger.info(f"🔀 Router Decision for {user_id}: {decision['route']}")
    
    return {"router_decision": decision}

async def inventory_node(state: AgentState):
    """
    Step 2a: Inventory Worker (SQL).
    """
    decision = state.get("router_decision", {})
    params = decision.get("parameters", {})
    query = params.get("query", "")
    
    # Get Location from Frontend Metadata (Critical for "Nearby")
    meta = state.get("request_metadata", {})
    lat = meta.get("lat")
    lng = meta.get("lng")
    
    logger.info(f"📦 Inventory Check: '{query}' near {lat},{lng}")
    
    try:
        # Call your existing service (Pure SQL/Code)
        # Note: If embedding cost is an issue, ensure search_products handles embedding=None
        results = CatalogService.search_products(query, limit=4)
        
        # If location is provided, filter or annotate with stock
        # (Assuming CatalogService returns a list of dicts)
        if not results:
            output = "No products found matching that description."
        else:
            output = json.dumps(results)
            
    except Exception as e:
        logger.error(f"Inventory Error: {e}")
        output = "Error checking inventory."

    return {"tool_output": output}

async def support_node(state: AgentState):
    """
    Step 2b: Support Worker (SQL).
    """
    user_id = state.get("user_id")
    if not user_id or user_id == "guest":
        return {"tool_output": "User is guest. Cannot check orders."}
        
    logger.info(f"🎫 Checking Orders for {user_id}")
    
    try:
        # Fetch recent orders via Supabase
        orders = supabase.table("orders")\
            .select("id, status, total_amount, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(3)\
            .execute()
            
        if not orders.data:
            output = "No recent orders found."
        else:
            output = json.dumps(orders.data)
            
    except Exception as e:
        logger.error(f"Support Error: {e}")
        output = "Error fetching order history."
        
    return {"tool_output": output}

async def loyalty_node(state: AgentState):
    """
    Step 2c: Loyalty Worker.
    (We already fetched context in Router, but this node can fetch deeper details if needed)
    """
    user_id = state.get("user_id")
    context = await RouterService.get_loyalty_context(user_id)
    return {"tool_output": context}

async def synthesizer_node(state: AgentState):
    """
    Step 3: The Polisher (Gemini).
    """
    tool_data = state.get("tool_output", "No specific data.")
    router_data = state.get("router_decision", {})
    user_msg = state["messages"][-1].content
    
    intent = router_data.get("route", "general")
    
    # System Prompt Injection
    system_prompt = f"""
    You are Daksha, a helpful Retail AI Assistant.
    
    CURRENT SITUATION:
    - User Intent: {intent}
    - User Query: "{user_msg}"
    - Data Retrieved from System: {tool_data}
    
    INSTRUCTIONS:
    1. Answer the user's query utilizing the Data Retrieved.
    2. If the data is a JSON list of products, summarize them briefly (e.g., "I found these options...").
       - DO NOT list every single detail textually. The UI will show cards.
    3. If the data is empty/error, apologize politely.
    4. Keep the tone friendly and concise.
    """
    
    try:
        llm = AIService.get_llm() # Returns Gemini ChatModel
        response = await llm.ainvoke([SystemMessage(content=system_prompt)])
        return {"messages": [response]}
        
    except Exception as e:
        logger.error(f"Synthesizer Error: {e}")
        return {"messages": [AIMessage(content="I'm having trouble formulating a response right now.")]}

# --- 3. EDGES & GRAPH ---

def route_decision(state: AgentState):
    """
    The Switchboard Logic.
    """
    route = state["router_decision"].get("route", "synthesizer")
    
    if route == "inventory": return "inventory_agent"
    if route == "support": return "support_agent"
    if route == "loyalty": return "loyalty_agent"
    
    return "synthesizer" # Fallback skips workers

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("inventory_agent", inventory_node)
workflow.add_node("support_agent", support_node)
workflow.add_node("loyalty_agent", loyalty_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "inventory_agent": "inventory_agent",
        "support_agent": "support_agent",
        "loyalty_agent": "loyalty_agent",
        "synthesizer": "synthesizer"
    }
)

# Workers always go to Synthesizer
workflow.add_edge("inventory_agent", "synthesizer")
workflow.add_edge("support_agent", "synthesizer")
workflow.add_edge("loyalty_agent", "synthesizer")
workflow.add_edge("synthesizer", END)

# Compile
daksha_graph = workflow.compile()
