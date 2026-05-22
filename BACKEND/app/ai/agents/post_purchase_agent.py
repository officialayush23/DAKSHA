# app/ai/agents/post_purchase_agent.py
"""
PostPurchaseAgent — Groq llama-3.3-70b
Handles returns, exchanges, grievances, refund status.
Policy validators are called inside tools to enforce business rules.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage
from app.ai.llm import get_llm_for_agent
from app.ai.message_utils import trim_messages_for_groq
from app.ai.state import AgentState
from app.ai.policy.company_policy import build_agent_prompt
from app.ai.tools.support_tools import (
    process_return,
    view_returns,
    cancel_return_request_tool,
    process_exchange,
    view_exchanges,
    request_order_cancel,
    create_complaint,
    view_complaints,
    request_human_handoff,
)

POST_PURCHASE_INSTRUCTIONS = """
You handle everything after an order is placed: returns, exchanges, order cancellations, and grievances.

CAPABILITIES:
  • view_returns              — show existing return requests
  • process_return            — initiate a new return request
  • cancel_return_request_tool — cancel an existing return request
  • view_exchanges            — show existing exchange requests
  • process_exchange          — initiate a new exchange (size / colour / defect)
  • request_order_cancel      — cancel an order (before shipped)
  • create_complaint          — log a formal grievance
  • view_complaints           — show open complaints
  • request_human_handoff     — escalate to human agent

RETURN POLICY REMINDERS:
• Within 7 days of delivery. Unworn. Original tags attached.
• Excluded: innerwear, swimwear, lingerie, personalised items.
• Final-sale items (>50% discount) — not returnable.
• Maximum 1 return per order.

EXCHANGE POLICY REMINDERS:
• Within 14 days of delivery.
• Reasons: size, color, defect, wrong item.

CANCELLATION REMINDERS:
• Free before 'packed'. ₹50 fee if packed. Not allowed after 'shipped'.

RULES:
1. Always ask for the ORDER ID before processing any return/exchange/cancellation.
2. Show existing requests (view_returns / view_exchanges) first — don't create duplicates.
3. For complaints, ask: what happened, when, and what resolution they expect.
4. If the user is very upset, call request_human_handoff.
5. After any action, confirm what was done and what the next steps are.
6. Wrap return/exchange status data in <UI_DATA> ... </UI_DATA> tags.

User ID: {user_id}
Session ID: {session_id}
"""

post_purchase_tools = [
    view_returns,
    process_return,
    cancel_return_request_tool,
    view_exchanges,
    process_exchange,
    request_order_cancel,
    create_complaint,
    view_complaints,
    request_human_handoff,
]

_llm = get_llm_for_agent("PostPurchaseAgent").bind_tools(post_purchase_tools)
_llm_text = get_llm_for_agent("PostPurchaseAgent")

_prompt = ChatPromptTemplate.from_messages([
    ("system", build_agent_prompt("Post-Purchase Agent", POST_PURCHASE_INSTRUCTIONS)),
    MessagesPlaceholder(variable_name="messages"),
])

_chain = _prompt | _llm
_chain_text = _prompt | _llm_text


def post_purchase_agent_node(state: AgentState) -> dict:
    messages = trim_messages_for_groq(state["messages"])
    ctx = {
        "messages": messages,
        "user_id": state.get("user_id", ""),
        "session_id": state.get("session_id", ""),
    }
    if messages and isinstance(messages[-1], ToolMessage):
        response = _chain_text.invoke(ctx)
    else:
        response = _chain.invoke(ctx)
    return {"messages": [response], "current_agent": "PostPurchaseAgent"}
