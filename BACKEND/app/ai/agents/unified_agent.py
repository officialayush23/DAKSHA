# app/ai/agents/unified_agent.py
"""
DAKSHA Unified Agent — single Gemini agent with ALL tools.
LLM is lazily initialised on first call to avoid OOM on Render free tier.
"""
import threading
from langchain_core.messages import ToolMessage
from app.ai.llm import get_gemini
from app.ai.state import AgentState
from app.ai.message_utils import trim_messages_for_groq

from app.ai.tools.recommendation_tools import (
    recommend_products, search_for_items, find_similar_by_image, get_trending_products,
)
from app.ai.tools.checkout_tools import (
    view_cart, add_to_cart, update_cart_quantity, remove_from_cart,
    start_delivery_checkout, start_pickup_checkout,
)
from app.ai.tools.inventory_tools import (
    check_item_stock, find_nearest_pickup_stores, agent_reschedule_delivery,
)
from app.ai.tools.loyalty_tools import (
    get_loyalty_balance, get_checkout_coupons, apply_discount_code,
    generate_personalized_offer, list_available_offers,
)
from app.ai.tools.support_tools import (
    request_human_handoff, process_return, view_returns, cancel_return_request_tool,
    process_exchange, view_exchanges, request_order_cancel, create_complaint, view_complaints,
)
from app.ai.tools.user_tools import get_user_profile, get_user_saved_addresses
from app.ai.tools.order_tools import get_user_orders, get_order_details

ALL_TOOLS = [
    recommend_products, search_for_items, find_similar_by_image, get_trending_products,
    view_cart, add_to_cart, update_cart_quantity, remove_from_cart,
    start_delivery_checkout, start_pickup_checkout,
    check_item_stock, find_nearest_pickup_stores, agent_reschedule_delivery,
    get_loyalty_balance, get_checkout_coupons, apply_discount_code,
    generate_personalized_offer, list_available_offers,
    process_return, view_returns, cancel_return_request_tool,
    process_exchange, view_exchanges, request_order_cancel,
    create_complaint, view_complaints, request_human_handoff,
    get_user_orders, get_order_details,
    get_user_profile, get_user_saved_addresses,
]

SYSTEM_PROMPT = (
    "You are Daksha, an AI fashion concierge for a premium e-commerce platform.\n\n"
    "You have access to every tool needed to help the user:\n"
    "  - Browse & discover products (recommendations, search, image search, trending)\n"
    "  - Manage their cart (view, add, remove, update quantities)\n"
    "  - Check stock and find pickup stores\n"
    "  - Apply offers, coupons, loyalty points\n"
    "  - Start checkout (delivery or in-store pickup)\n"
    "  - Track orders, reschedule deliveries\n"
    "  - Process returns, exchanges, complaints\n"
    "  - View their profile, orders, saved addresses\n"
    "  - Escalate to a human agent when needed\n\n"
    "IMAGE SEARCH:\n"
    "  When the user sends an image (or an image_url is in the message), ALWAYS call\n"
    "  find_similar_by_image with that URL to show visually similar products.\n"
    "  Then ask if they want to refine by color, size, or price.\n\n"
    "PRODUCT vs VARIANT - CRITICAL:\n"
    "  Every item in this catalog is a ProductVariant, not just a Product.\n"
    "  A single product (e.g. 'Mid-Rise Straight Jeans') can have MULTIPLE variants,\n"
    "  each with a unique variant_id, color, and size. When you call search_for_items,\n"
    "  recommend_products, or get_trending_products, EVERY returned item has its own\n"
    "  variant_id, color, and size. You MUST:\n"
    "    - Always use the exact variant_id when calling add_to_cart.\n"
    "    - Never call add_to_cart using only a product name - you need the variant_id.\n"
    "    - When the user says 'add the first one' or 'the blue one', look up the\n"
    "      variant_id from the most recently shown product list and use it directly.\n"
    "    - When multiple variants of the same product name appear, tell the user the\n"
    "      distinguishing detail (e.g. 'Mid-Rise Jeans - Black / M' vs '- Blue / L')\n"
    "      and confirm before adding.\n"
    "    - Recommendation/search tools already return IN-STOCK variants only.\n"
    "      Do NOT call check_item_stock before add_to_cart for items from those tools.\n"
    "      Only call check_item_stock if the user explicitly asks about a specific variant.\n"
    "    - Never show raw UUIDs to the user - use color + size + product name instead.\n\n"
    "RULES:\n"
    "1. After any cart change, call view_cart to show the updated cart.\n"
    "2. Wrap cart/product/order data in <UI_DATA>{{...}}</UI_DATA> tags for the UI to render.\n"
    "3. Be warm, concise, and helpful - one clear action at a time.\n"
    "4. Use request_human_handoff only if the user is clearly frustrated or explicitly asks.\n"
    "5. Never make up order IDs, prices, or product names - use the tools.\n\n"
    "Current user ID: {user_id}\n"
    "Current session ID: {session_id}\n"
    "Channel: {channel}\n"
    "Order mode: {order_mode}\n"
    "User context: {user_summary}\n"
)

# ── Lazy LLM singleton ─────────────────────────────────────────────────────────
# _llm is NOT created at import time — avoids OOM on Render free tier (512MB).
# It is initialised on the first chat request and cached for all subsequent calls.
_llm = None
_llm_lock = threading.Lock()


def _get_llm():
    global _llm
    if _llm is None:
        with _llm_lock:
            if _llm is None:  # double-checked locking
                _llm = get_gemini(temperature=0.2).bind_tools(ALL_TOOLS)
    return _llm


def unified_agent_node(state: AgentState) -> dict:
    """Single agent node — replaces orchestrator + all specialist agents."""
    from langchain_core.messages import SystemMessage

    messages = trim_messages_for_groq(state["messages"], keep_last=10)

    system_content = SYSTEM_PROMPT.format(
        user_id=state.get("user_id", ""),
        session_id=state.get("session_id", ""),
        channel=state.get("channel", "web"),
        order_mode=state.get("order_mode", "online"),
        user_summary=state.get("user_summary") or "New user - no prior context.",
    )

    full_messages = [SystemMessage(content=system_content)] + messages
    response = _get_llm().invoke(full_messages)

    return {
        "messages": [response],
        "current_agent": "UnifiedAgent",
    }
