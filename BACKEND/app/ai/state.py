# app/ai/state.py
from typing import TypedDict, List, Optional, Dict, Any, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class AgentState(TypedDict):
    # ── Conversation ──────────────────────────────────────────────────────────
    messages: Annotated[List[BaseMessage], add_messages]

    # ── Identity & Session ────────────────────────────────────────────────────
    user_id: str
    session_id: str
    channel: str                                        # web | kiosk | app
    order_mode: Literal["online", "pickup"]             # delivery vs walk-in

    # ── Long-term Memory ──────────────────────────────────────────────────────
    user_summary: Optional[str]                         # profile + behaviour summary
    conversation_summary: Optional[str]                 # summary of current session
    context_data: Dict[str, Any]                        # arbitrary bag from DB
    loyalty_tier: Optional[str]                         # bronze|silver|gold|platinum

    # ── Routing & Control ─────────────────────────────────────────────────────
    current_agent: Optional[str]                        # last agent that ran
    failure_count: int                                  # consecutive tool/agent failures
    pending_human_input: bool                           # True = AI paused, human handling

    # ── Human Handoff ─────────────────────────────────────────────────────────
    active_handoff_id: Optional[str]                    # FK → agent_handoffs.id

    # ── Recommendation Clarification Loop ─────────────────────────────────────
    clarification_context: Dict[str, Any]               # accumulates answers from user
    clarification_turn: int                             # how many clarifying Q's asked so far

    # ── Agent Action Logging ──────────────────────────────────────────────────
    # Each entry: {agent, tool, input, output, latency_ms, model, success}
    agent_tool_calls: List[Dict[str, Any]]

    # ── Kiosk ─────────────────────────────────────────────────────────────────
    kiosk_store_id: Optional[str]                       # selected store for pickup