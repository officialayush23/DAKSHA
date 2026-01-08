# app/agents/graph.py

import operator
import re
import json
from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.agents.confidence import ConfidenceScorer
from app.services.human_handoff_service import HumanHandoffService
from app.services.ai_service import AIService
from app.services.chat_history_service import ChatHistoryService 
from app.services.embeddings_worker import EmbeddingsWorker
from app.services.promotion_service import PromotionService
from app.core.database import supabase
from app.agents.budget import AgentBudgetEnforcer
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

# --------------------------------------------------
# CONTROL FLOW
# --------------------------------------------------

def should_continue(state: AgentState):
    """
    Determines whether to route to tools or stop.
    """
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"
    return END

# ==============================================================================
# 🧠 AGENT NODE
# ==============================================================================
from app.agents.intent_classifier import IntentClassifier

async def agent_node(state: AgentState):
    messages = state["messages"]
    user_id = state["user_id"]

    last_user_msg = messages[-1].content

    # 🔀 Intent detection (DeepSeek)
    intent = await IntentClassifier.classify(last_user_msg)

    system_prompt = f"""
You are Daksha, an expert AI Retail Agent.

Detected intent: {intent}

Rules:
- If intent is human_handoff → immediately escalate
- If intent is support → prioritize resolution
- If intent is checkout → minimize verbosity
- Use tools only when needed
"""

    if messages and isinstance(messages[0], SystemMessage):
        messages[0] = SystemMessage(content=system_prompt)
    else:
        messages = [SystemMessage(content=system_prompt)] + messages

    response = primary_llm.invoke(messages)
    return {"messages": [response]}

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


async def run_sales_agent(
    user_id: str | None,
    channel: str,
    channel_id: str,
    message: str
):
    print(f"🤖 [Agent] {user_id} | {message}")

    # --------------------------------------------------
    # 1. Session
    # --------------------------------------------------
    session_id = ChatHistoryService.get_or_create_session(
        user_id, channel, channel_id
    )

    # --------------------------------------------------
    # 2. Save USER message
    # --------------------------------------------------
    ChatHistoryService.save_message(
        session_id,
        "user",
        message
    )

    # --------------------------------------------------
    # 3. Load history → LangChain messages
    # --------------------------------------------------
    raw_history = ChatHistoryService.load_history(session_id, limit=6)
    history_msgs = []

    for m in raw_history:
        if m["role"] == "user":
            history_msgs.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            history_msgs.append(AIMessage(content=m["content"]))

    # --------------------------------------------------
    # 4. Run graph
    # --------------------------------------------------
    inputs = {
        "messages": history_msgs + [HumanMessage(content=message)],
        "user_id": user_id or "guest",
        "channel": channel,
        "session_id": session_id,
    }

    try:
        final_state = await daksha_graph.ainvoke(inputs)

        all_msgs = final_state["messages"]
        last_msg = all_msgs[-1]
        final_text = last_msg.content or "I processed that."

        # --------------------------------------------------
        # 5. Extract tool payload
        # --------------------------------------------------
        payload = None
        tool_used = None

        for msg in reversed(all_msgs):
            if isinstance(msg, ToolMessage):
                tool_used = msg.name
                try:
                    data = json.loads(msg.content)

                    if msg.name in (
                        "search_products_tool",
                        "get_personalized_recommendations_tool",
                    ):
                        if isinstance(data, list) and data:
                            payload = {"type": "products", "data": data}
                            final_text = "Here are the best options for you."

                    elif msg.name == "get_order_history_tool":
                        payload = {"type": "order_history", "data": data}

                    if payload:
                        break
                except Exception:
                    pass

        # --------------------------------------------------
        # 6. Save AI message
        # --------------------------------------------------
        ChatHistoryService.save_message(
            session_id,
            "assistant",
            final_text,
            tool_used=tool_used,
            payload=payload,
        )

        # --------------------------------------------------
        # 7. Update embeddings (async-safe)
        # --------------------------------------------------
        if user_id and user_id != "guest":
            EmbeddingsWorker.compute_and_upsert_user_embedding(user_id)

        # --------------------------------------------------
        # 8. Confidence scoring
        # --------------------------------------------------
        confidence = ConfidenceScorer.score(all_msgs)

        # --------------------------------------------------
        # 9. Agent budget enforcement (soft)
        # --------------------------------------------------
        AgentBudgetEnforcer.track(
            agent_name="sales_agent",
            session_id=session_id,
            confidence=confidence,
        )

        # --------------------------------------------------
        # 10. Auto human handoff
        # --------------------------------------------------
        if confidence < 0.4:
            HumanHandoffService.trigger(
                session_id=session_id,
                user_id=user_id,
                reason="low_confidence",
                summary=final_text,
                metadata={
                    "confidence": confidence,
                    "last_tool": tool_used,
                },
            )

        # --------------------------------------------------
        # 11. Log agent run
        # --------------------------------------------------
        try:
            # Get agent name from agents table or use default
            agent_name = "Daksha Sales Agent"
            try:
                agent = supabase.table("agents").select("name").eq("name", "Daksha Sales Agent").maybe_single().execute()
                if not agent.data:
                    # Create agent if doesn't exist
                    # In Supabase v2, insert() already returns data - no need for .select()
                    supabase.table("agents").insert({
                        "name": "Daksha Sales Agent",
                        "description": "Primary conversational AI agent for retail",
                        "responsibility": "sales",
                        "is_active": True
                    }).execute()
            except:
                pass
            
            # In Supabase v2, insert() already returns data - no need for .select()
            supabase.table("agent_runs").insert(
                {
                    "conversation_id": session_id,  # session_id is conversation_sessions.id
                    "user_id": user_id if user_id != "guest" else None,
                    "agent_name": agent_name,
                    "trigger": "chat",  # agent_trigger_enum: chat, system, cron, webhook
                    "input_summary": message[:500],  # Truncate if too long
                    "output_summary": final_text[:500],
                    "success": True,
                }
            ).execute()
        except Exception as e:
            print(f"Failed to log agent run: {e}")
            pass

        return {
            "reply": final_text,
            "payload": payload,
            "confidence": confidence,
            "conversation_id": session_id,  # session_id is conversation_sessions.id
        }

    except Exception as e:
        print(f"❌ Agent failure: {e}")
        return {
            "reply": "I'm having trouble connecting. Please try again.",
            "payload": None,
            "confidence": 0.0,
        }