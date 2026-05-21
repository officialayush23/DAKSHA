# app/ai/agents/payment_agent.py
"""
PaymentAgent — Groq llama-3.3-70b
Drives the checkout state machine: validate cart → reserve stock →
lock price → apply offers → initiate payment → confirm order.
Maps exactly onto CheckoutStateEnum.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage
from app.ai.llm import get_llm_for_agent
from app.ai.state import AgentState
from app.ai.policy.company_policy import build_agent_prompt
from app.ai.tools.checkout_tools import (
    view_cart,
    start_delivery_checkout,
    start_pickup_checkout,
    finalize_payment,
)
from app.ai.tools.loyalty_tools import (
    get_checkout_coupons,
    apply_discount_code,
    get_loyalty_balance,
)
from app.ai.tools.inventory_tools import find_nearest_pickup_stores

PAYMENT_INSTRUCTIONS = """
You guide the user through the checkout and payment flow.

CHECKOUT STATE MACHINE (follow in order):
  1. view_cart                → confirm items and total
  2. start_delivery_checkout  → for online orders (creates checkout session, reserves stock)
     OR start_pickup_checkout → for in-store pickup (user must select a store)
  3. get_checkout_coupons     → show applicable offers (call proactively)
  4. apply_discount_code      → if user wants to use a coupon or offer
  5. finalize_payment         → collect payment method, complete order

RULES:
1. Always show cart summary BEFORE initiating checkout.
2. For pickup mode, call find_nearest_pickup_stores first so user can pick a store.
3. After stock reservation fails, apologise and route back to CartAgent suggestion.
4. After payment fails {payment_max_retry} times, escalate to Handoff.
5. On success, wrap the order confirmation in <UI_DATA> ... </UI_DATA> tags.
6. Never ask for card numbers — payment is handled by the payment gateway.
   Just confirm the method (card/UPI/COD) and call finalize_payment.
7. COD only available for orders ≤₹5000.

User ID: {user_id}
Session ID: {session_id}
Order mode: {order_mode}
Kiosk store ID: {kiosk_store_id}
"""

payment_tools = [
    view_cart,
    start_delivery_checkout,
    start_pickup_checkout,
    finalize_payment,
    get_checkout_coupons,
    apply_discount_code,
    get_loyalty_balance,
    find_nearest_pickup_stores,
]

_llm = get_llm_for_agent("PaymentAgent").bind_tools(payment_tools)
_llm_text = get_llm_for_agent("PaymentAgent")

_prompt = ChatPromptTemplate.from_messages([
    ("system", build_agent_prompt("Payment Agent", PAYMENT_INSTRUCTIONS)),
    MessagesPlaceholder(variable_name="messages"),
])

_chain = _prompt | _llm
_chain_text = _prompt | _llm_text


def payment_agent_node(state: AgentState) -> dict:
    from app.ai.policy.company_policy import PAYMENT_POLICY
    messages = state["messages"]
    ctx = {
        "messages": messages,
        "user_id": state.get("user_id", ""),
        "session_id": state.get("session_id", ""),
        "order_mode": state.get("order_mode", "online"),
        "kiosk_store_id": state.get("kiosk_store_id", ""),
        "payment_max_retry": PAYMENT_POLICY.max_payment_retry_attempts,
    }
    if messages and isinstance(messages[-1], ToolMessage):
        response = _chain_text.invoke(ctx)
    else:
        response = _chain.invoke(ctx)
    return {"messages": [response], "current_agent": "PaymentAgent"}
