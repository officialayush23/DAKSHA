# app/ai/agents/support_agent.py
"""
SupportAgent — Groq llama-3.3-70b
General support: account, orders history, policy FAQ, escalation.
Note: Returns/exchanges/cancellations are handled by PostPurchaseAgent.
      This agent handles questions, account issues, and general help.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage
from app.ai.llm import get_llm_for_agent
from app.ai.message_utils import trim_messages_for_groq
from app.ai.state import AgentState
from app.ai.policy.company_policy import build_agent_prompt
from app.ai.tools.support_tools import (
    view_complaints,
    create_complaint,
    request_human_handoff,
)
from app.ai.tools.user_tools import get_user_profile, get_user_saved_addresses

SUPPORT_INSTRUCTIONS = """
You handle general customer support queries. Be warm, concise, and helpful.

CAPABILITIES:
  • get_user_profile         — look up account details, order history
  • get_user_saved_addresses — show saved delivery addresses
  • view_complaints          — show existing complaints
  • create_complaint         — log a new formal complaint
  • request_human_handoff    — escalate to human agent

WHAT YOU HANDLE:
  ✓ Account information and profile questions
  ✓ Order history lookup
  ✓ Policy FAQs (returns, delivery, payments — you know the policy)
  ✓ Formal complaint logging
  ✗ Returns / exchanges → tell user to say "I want to return an item" (PostPurchaseAgent)
  ✗ Tracking → tell user to say "track my order" (DeliveryAgent)
  ✗ Payments → tell user to say "I want to checkout" (PaymentAgent)

RULES:
1. Answer policy questions directly from your knowledge — no tool needed.
2. If the question is about order status, use get_user_profile to retrieve orders.
3. Escalate immediately if the user uses strong negative language or explicitly asks for human.
4. Always close with "Is there anything else I can help with?"

User ID: {user_id}
User summary: {user_summary}
"""

support_tools = [
    get_user_profile,
    get_user_saved_addresses,
    view_complaints,
    create_complaint,
    request_human_handoff,
]

_llm = get_llm_for_agent("SupportAgent").bind_tools(support_tools)
_llm_text = get_llm_for_agent("SupportAgent")

_prompt = ChatPromptTemplate.from_messages([
    ("system", build_agent_prompt("Support Agent", SUPPORT_INSTRUCTIONS)),
    MessagesPlaceholder(variable_name="messages"),
])

_chain = _prompt | _llm
_chain_text = _prompt | _llm_text


def support_agent_node(state: AgentState) -> dict:
    messages = trim_messages_for_groq(state["messages"])
    ctx = {
        "messages": messages,
        "user_id": state.get("user_id", ""),
        "session_id": state.get("session_id", ""),
        "user_summary": state.get("user_summary", "New user."),
    }
    if messages and isinstance(messages[-1], ToolMessage):
        response = _chain_text.invoke(ctx)
    else:
        response = _chain.invoke(ctx)
    return {"messages": [response], "current_agent": "SupportAgent"}