# app/ai/agents/unified_agent.py
"""
DAKSHA Unified Agent — single Gemini agent with ALL tools.

Replaces the fragile multi-agent supervisor routing.
Gemini 2.0 Flash handles intent, tool selection, and response in one pass.
"""
from langchain_core.messages import ToolMessage
from app.ai.llm import get_gemini
from app.ai.state import AgentState
from app.ai.message_utils import trim_messages_for_groq  # reused for context trimming

# ── Import every tool ──────────────────────────────────────────────────────────
from app.ai.tools.recommendation_tools import (
    recommend_products,
    search_for_items,
    find_similar_by_image,
    get_trending_products,
)
from app.ai.tools.checkout_tools import (
    view_cart,
    add_to_cart,
    update_cart_quantity,
    remove_from_cart,
    start_delivery_checkout,
    start_pickup_checkout,
)
from app.ai.tools.inventory_tools import (
    check_item_stock,
    find_nearest_pickup_stores,
    agent_reschedule_delivery,
)
from app.ai.tools.loyalty_tools import (
    get_loyalty_balance,
    get_checkout_coupons,
    apply_discount_code,
    generate_personalized_offer,
    list_available_offers,
)
from app.ai.tools.support_tools import (
    request_human_handoff,
    process_return,
    view_returns,
    cancel_return_request_tool,
    process_exchange,
    view_exchanges,
    request_order_cancel,
    create_complaint,
    view_complaints,
)
from app.ai.tools.user_tools import (
    get_user_profile,
    get_user_saved_addresses,
)

# ── All tools in one list ──────────────────────────────────────────────────────
ALL_TOOLS = [
    # Discovery
    recommend_products,
    search_for_items,
    find_similar_by_image,
    get_trending_products,
    # Cart
    view_cart,
    add_to_cart,
    update_cart_quantity,
    remove_from_cart,
    # Checkout
    start_delivery_checkout,
    start_pickup_checkout,
    # Inventory / Delivery
    check_item_stock,
    find_nearest_pickup_stores,
    agent_reschedule_delivery,
    # Offers / Loyalty
    get_loyalty_balance,
    get_checkout_coupons,
    apply_discount_code,
    generate_personalized_offer,
    list_available_offers,
    # Post-purchase / Support
    process_return,
    view_returns,
    cancel_return_request_tool,
    process_exchange,
    view_exchanges,
    request_order_cancel,
    create_complaint,
    view_complaints,
    request_human_handoff,
    # User
    get_user_profile,
    get_user_saved_addresses,
]

SYSTEM_PROMPT = """You are Daksha, an AI fashion concierge for a premium e-commerce platform.

You have access to every tool needed to help the user:
  • Browse & discover products (recommendations, search, image search, trending)
  • Manage their cart (view, add, remove, update quantities)
  • Check stock and find pickup stores
  • Apply offers, coupons, loyalty points
  • Start checkout (delivery or in-store pickup)
  • Track orders, reschedule deliveries
  • Process returns, exchanges, complaints
  • View their profile, orders, saved addresses
  • Escalate to a human agent when needed

RULES:
1. Always call check_item_stock before add_to_cart.
2. After any cart change, call view_cart to show the updated cart.
3. Wrap cart/product/order data in <UI_DATA>{{...}}</UI_DATA> tags for the UI to render.
4. Be warm, concise, and helpful — one clear action at a time.
5. Use request_human_handoff only if the user is clearly frustrated or explicitly asks for a human.
6. Never make up order IDs, prices, or product names — use the tools.

Current user ID: {user_id}
Current session ID: {session_id}
Channel: {channel}
Order mode: {order_mode}
User context: {user_summary}
"""

# Build the agent LLM with all tools bound once at module load
_llm = get_gemini(temperature=0.2).bind_tools(ALL_TOOLS)
_llm_text = get_gemini(temperature=0.2)  # no tools — for final text response after tool call


def unified_agent_node(state: AgentState) -> dict:
    """Single agent node — replaces orchestrator + all specialist agents."""
    from langchain_core.messages import SystemMessage

    messages = trim_messages_for_groq(state["messages"], keep_last=10)

    system_content = SYSTEM_PROMPT.format(
        user_id=state.get("user_id", ""),
        session_id=state.get("session_id", ""),
        channel=state.get("channel", "web"),
        order_mode=state.get("order_mode", "online"),
        user_summary=state.get("user_summary") or "New user — no prior context.",
    )

    full_messages = [SystemMessage(content=system_content)] + messages

    # After a tool result → use text-only LLM to compose the final reply
    if messages and isinstance(messages[-1], ToolMessage):
        response = _llm_text.invoke(full_messages)
    else:
        response = _llm.invoke(full_messages)

    return {
        "messages": [response],
        "current_agent": "UnifiedAgent",
    }
