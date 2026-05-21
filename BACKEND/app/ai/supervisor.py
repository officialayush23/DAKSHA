# app/ai/supervisor.py
"""
Orchestrator node — the brain of the DAKSHA multi-agent graph.

Uses Groq llama-3.3-70b for fast structured routing (RouteSchema).
Injects company policy + user context so routing respects business rules.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from app.ai.llm import get_groq
from app.ai.routing import RouteSchema, ORCHESTRATOR_SYSTEM_PROMPT
from app.ai.state import AgentState
from app.ai.policy.company_policy import HANDOFF_POLICY


def supervisor_node(state: AgentState) -> dict:
    """
    Analyzes conversation state and routes to the correct specialist agent.
    Returns a state update dict (never raises — failures fall back to SupportAgent).
    """
    # ── 1. Hard-wire escalation conditions ────────────────────────────────────
    failure_count = state.get("failure_count", 0)
    pending_human = state.get("pending_human_input", False)

    if pending_human:
        # Already in handoff — don't route to agents
        return {"current_agent": "Handoff"}

    if failure_count >= HANDOFF_POLICY.max_agent_failures_before_handoff:
        return {
            "current_agent": "Handoff",
            "messages": [AIMessage(
                content="I've had trouble helping you a few times. Let me connect you with our support team right away."
            )],
        }

    # ── 2. Check for explicit handoff keywords in latest message ──────────────
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            last_user_msg = (msg.content or "").lower()
            break

    for kw in HANDOFF_POLICY.trigger_keywords:
        if kw in last_user_msg:
            return {
                "current_agent": "Handoff",
                "messages": [AIMessage(
                    content="Of course! Let me connect you with a member of our team right now."
                )],
            }

    # ── 3. LLM routing ────────────────────────────────────────────────────────
    llm = get_groq(temperature=0.0).with_structured_output(RouteSchema)

    prompt = ChatPromptTemplate.from_messages([
        ("system", ORCHESTRATOR_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    try:
        decision: RouteSchema = chain.invoke({
            "messages": state["messages"],
            "user_summary": state.get("user_summary", "New user — no prior context."),
            "channel": state.get("channel", "web"),
            "order_mode": state.get("order_mode", "online"),
            "failure_count": failure_count,
        })
    except Exception as e:
        # Routing failure — fall back to SupportAgent rather than crashing
        return {
            "current_agent": "SupportAgent",
            "failure_count": failure_count + 1,
        }

    updates: dict = {"current_agent": decision.next_agent}

    # If FINISH, attach the Orchestrator's conversational reply
    if decision.next_agent == "FINISH" and decision.response:
        updates["messages"] = [AIMessage(content=decision.response)]

    return updates