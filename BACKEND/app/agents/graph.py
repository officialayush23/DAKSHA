# app/agents/graph.py

import operator
import re
import json
from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.services.ai_service import AIService
from app.services.chat_history_service import ChatHistoryService 
from app.services.embeddings_worker import EmbeddingsWorker
from app.services.promotion_service import PromotionService
from app.database import supabase

# Import ALL Tools
from app.agents.tools import (
    search_products_tool,
    get_personalized_recommendations_tool,
    find_nearest_store_tool,
    check_product_availability_nearby_tool,
    get_cart_tool,
    add_to_cart_tool,
    get_user_context_tool,
    checkout_tool,
    get_order_history_tool,
    track_order_tool,
    lodge_complaint_tool,
    handoff_to_human_tool,
    check_loyalty_tool
)

ALL_TOOLS = [
    search_products_tool,
    get_personalized_recommendations_tool,
    find_nearest_store_tool,
    check_product_availability_nearby_tool,
    get_cart_tool,
    add_to_cart_tool,
    get_user_context_tool,
    checkout_tool,
    get_order_history_tool,
    track_order_tool,
    lodge_complaint_tool,
    handoff_to_human_tool,
    check_loyalty_tool
]

llm = AIService.get_llm()
primary_llm = llm.bind_tools(ALL_TOOLS)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    channel: str
    session_id: str

# ==============================================================================
# 🧠 AGENT NODE
# ==============================================================================

def agent_node(state: AgentState):
    messages = state["messages"]
    user_id = state["user_id"]
    
    # 1. Fetch User Context
    context_str = "Guest"
    promo_str = ""
    
    if user_id != "guest":
        try:
            footprints = EmbeddingsWorker.fetch_recent_product_context(user_id, limit=5)
            if footprints:
                names = [f.get("event_data", {}).get("name") for f in footprints if f.get("event_data", {}).get("name")]
                context_str = ", ".join(names[:5])
        except: pass

    try:
        promos = PromotionService.get_active_promotions(limit=2)
        promo_str = ", ".join([p["code"] for p in promos])
    except: pass

    # 2. System Prompt
    system_prompt = f"""You are Daksha, the expert AI Retail Agent.

    USER CONTEXT:
    - ID: {user_id}
    - Recent Interests: {context_str}
    - Active Codes: {promo_str}

    CRITICAL INSTRUCTIONS:
    1. **Visuals**: If you find products, orders, or stores using tools, **DO NOT** list them in text. Just say "Here are the best options." The UI will render cards.
    2. **Tone**: Helpful, short, friendly.

    Be proactive. If stock is low, mention it.
    """

    if messages and isinstance(messages[0], SystemMessage):
        messages[0] = SystemMessage(content=system_prompt)
    else:
        messages = [SystemMessage(content=system_prompt)] + messages

    response = primary_llm.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# ==============================================================================
# 🕸️ GRAPH WIRING
# ==============================================================================

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(ALL_TOOLS))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")
daksha_graph = workflow.compile()

# ==============================================================================
# 🚀 RUNNER (Writes to YOUR Schema)
# ==============================================================================

async def run_sales_agent(user_id: str | None, channel: str, channel_id: str, message: str):
    print(f"🤖 [Agent] {user_id} | {message}")
    
    # 1. Get/Create Session (Using your `chat_sessions` schema)
    session_id = ChatHistoryService.get_or_create_session(user_id, channel, channel_id)

    # 2. Save USER Message (Using `chat_messages` schema)
    ChatHistoryService.save_message(session_id, "user", message)

    # 3. Load History
    # We load raw dicts from service, convert to LangChain Objects
    raw_history = ChatHistoryService.load_history(session_id, limit=6)
    history_msgs = []
    for m in raw_history:
        if m['role'] == 'user': history_msgs.append(HumanMessage(content=m['content']))
        elif m['role'] == 'assistant': history_msgs.append(AIMessage(content=m['content']))

    # 4. Run Graph
    inputs = {
        "messages": history_msgs + [HumanMessage(content=message)], 
        "user_id": user_id or "guest", 
        "channel": channel, 
        "session_id": session_id
    }

    try:
        final_state = await daksha_graph.ainvoke(inputs)
        all_msgs = final_state["messages"]
        last_msg = all_msgs[-1]
        final_text = last_msg.content or "I processed that."
        
        # 5. Extract Payload & Tool Name
        payload = None
        tool_used = None
        
        for msg in reversed(all_msgs):
            if isinstance(msg, ToolMessage):
                try:
                    data = json.loads(msg.content)
                    tool_used = msg.name # Save the tool name to DB
                    
                    # 🛍️ Products
                    if msg.name in ["search_products_tool", "get_personalized_recommendations_tool"]:
                        if isinstance(data, list) and data: 
                            payload = {"type": "products", "data": data}
                            # Clean text for TTS
                            if "json" in final_text.lower() or "[" in final_text:
                                final_text = "Here are the best matches I found for you."

                    # 📦 Orders / Other tools
                    elif msg.name == "get_order_history_tool":
                        payload = {"type": "order_history", "data": data}
                    
                    if payload: break
                except: pass

        # 6. Save AI Message (With Metadata!)
        # We pass `payload` to `metadata` column and `tool_used` to `tool_used` column
        ChatHistoryService.save_message(session_id, "assistant", final_text, tool_used=tool_used, payload=payload)

        # 7. Update Embeddings (Background)
        if user_id and user_id != "guest":
            EmbeddingsWorker.compute_and_upsert_user_embedding(user_id)

        # 8. Log Agent Run
        # (Optional: keep this table if you still want raw run logs, otherwise chat_messages handles history)
        try:
            supabase.table("agent_runs").insert({
                "session_id": session_id,
                "user_id": user_id if user_id != "guest" else None,
                "agent_name": "Daksha v2",
                "input_summary": message,
                "output_summary": final_text,
                "tool_calls": payload
            }).execute()
        except: pass

        return {"reply": final_text, "payload": payload}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"reply": "I'm having trouble connecting. Try again.", "payload": None}