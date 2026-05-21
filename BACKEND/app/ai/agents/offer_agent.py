# app/ai/agents/offer_agent.py
"""
OfferAgent — Gemini 2.5 Flash
Personalised offer generation, coupon suggestion, loyalty point advice.
Policy layer hard-caps all discounts.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage
from app.ai.llm import get_llm_for_agent
from app.ai.state import AgentState
from app.ai.policy.company_policy import build_agent_prompt
from app.ai.tools.loyalty_tools import (
    get_loyalty_balance,
    get_checkout_coupons,
    apply_discount_code,
    generate_personalized_offer,
    list_available_offers,
)

OFFER_INSTRUCTIONS = """
You help users discover and apply the best offers available to them.

CAPABILITIES:
  • list_available_offers    — show all active coupons + personalized offers
  • get_loyalty_balance      — check points balance and tier
  • generate_personalized_offer — create a NEW tailored offer (subject to policy caps)
  • get_checkout_coupons     — coupons applicable to the current cart
  • apply_discount_code      — apply a coupon code

RULES:
1. Always call get_loyalty_balance first to know the user's tier before generating offers.
2. NEVER promise or generate a discount above the policy maximum for the user's tier.
   The policy caps are: Bronze=10%, Silver=15%, Gold=20%, Platinum=30%.
3. If the user already has 3+ active offers, do NOT generate more — list existing ones instead.
4. Wrap offer lists in <UI_DATA> ... </UI_DATA> tags for UI rendering.
5. If the user wants to apply an offer at checkout, use apply_discount_code.
   For checkout-level application, tell them to proceed to checkout and the offer will be applied.
6. Be enthusiastic but honest — never invent discounts that don't exist.

User ID: {user_id}
Session ID: {session_id}
Loyalty Tier: {loyalty_tier}
"""

offer_tools = [
    list_available_offers,
    get_loyalty_balance,
    generate_personalized_offer,
    get_checkout_coupons,
    apply_discount_code,
]

_llm = get_llm_for_agent("OfferAgent").bind_tools(offer_tools)
_llm_text = get_llm_for_agent("OfferAgent")

_prompt = ChatPromptTemplate.from_messages([
    ("system", build_agent_prompt("Offer Agent", OFFER_INSTRUCTIONS)),
    MessagesPlaceholder(variable_name="messages"),
])

_chain = _prompt | _llm
_chain_text = _prompt | _llm_text


def offer_agent_node(state: AgentState) -> dict:
    messages = state["messages"]
    ctx = {
        "messages": messages,
        "user_id": state.get("user_id", ""),
        "session_id": state.get("session_id", ""),
        "loyalty_tier": state.get("loyalty_tier", "default"),
    }
    if messages and isinstance(messages[-1], ToolMessage):
        response = _chain_text.invoke(ctx)
    else:
        response = _chain.invoke(ctx)
    return {"messages": [response], "current_agent": "OfferAgent"}
