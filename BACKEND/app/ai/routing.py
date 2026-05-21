# app/ai/routing.py
# Orchestrator routing schema — all 8 specialist agents + FINISH + Handoff
from pydantic import BaseModel, Field
from typing import Literal, Optional


class RouteSchema(BaseModel):
    next_agent: Literal[
        "FINISH",
        # ── Discovery ──────────────────────────────────────────────
        "RecommendationAgent",      # product discovery, image search, trending, conversational recs
        # ── Commerce ───────────────────────────────────────────────
        "CartAgent",                # add/remove/update/view cart
        "OfferAgent",               # personalized offers, coupon suggestion, loyalty advice
        "PaymentAgent",             # checkout initiation, payment, apply offers at checkout
        # ── Fulfilment & Post-sale ─────────────────────────────────
        "DeliveryAgent",            # tracking, delay, reschedule, delivery support
        "PostPurchaseAgent",        # returns, exchanges, grievances
        # ── Support ────────────────────────────────────────────────
        "SupportAgent",             # general FAQ, account, policy questions
        # ── Escalation ─────────────────────────────────────────────
        "Handoff",                  # human handoff — use when AI cannot help
    ] = Field(description="The next agent to route the conversation to.")

    reasoning: str = Field(
        description="One sentence explaining why this agent was chosen."
    )
    response: Optional[str] = Field(
        default=None,
        description=(
            "Populated ONLY when next_agent='FINISH'. "
            "A warm, helpful conversational reply to the user. "
            "Leave null for all other routes."
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator for DAKSHA, an agent-first fashion e-commerce platform.

Your ONLY job is to read the user's latest message, understand their intent, and route to the correct specialist agent.
You do NOT answer the user directly — except when next_agent='FINISH'.

ROUTING RULES:
──────────────────────────────────────────────────────────────────
• RecommendationAgent  → finding products, outfit ideas, image search, trending, "what should I buy", "suggest me", "similar to this photo"
• CartAgent            → "add to cart", "remove from cart", "what's in my cart", "update quantity", "clear cart"
• OfferAgent           → "any discounts?", "apply coupon", "use my points", "do I have any offers?", loyalty queries
• PaymentAgent         → "checkout", "pay now", "complete my order", "apply offer at checkout", payment method queries
• DeliveryAgent        → "where is my order?", "track", "reschedule delivery", "delivery delayed", "change delivery date"
• PostPurchaseAgent    → "return", "exchange", "refund", "wrong size", "defective item", "file a complaint"
• SupportAgent         → general FAQs, account issues, order history, policy questions not covered above
• Handoff              → user is angry / frustrated, explicitly asks for human, 3+ consecutive failures
• FINISH               → greeting, small talk, order completed, conversation naturally ended — reply warmly

CRITICAL:
- Route to exactly ONE agent.
- If intent is ambiguous between CartAgent and PaymentAgent, prefer CartAgent.
- Never route to Handoff unless genuinely needed — it interrupts the AI flow.
- When you choose FINISH, always populate the 'response' field.

User channel: {channel}
Order mode: {order_mode}
User summary: {user_summary}
Failure count this session: {failure_count}
"""