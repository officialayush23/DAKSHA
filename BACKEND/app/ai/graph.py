# app/ai/graph.py
"""
DAKSHA Agent Graph — Unified Single-Agent Pattern
══════════════════════════════════════════════════

  START → unified_agent → tools (if tool calls) → unified_agent → … → END

Single Gemini agent with all tools bound.
Replaces the fragile multi-agent supervisor routing.
"""
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.ai.state import AgentState
from app.ai.agents.unified_agent import unified_agent_node, ALL_TOOLS
from app.ai.logging_nodes import make_logging_tool_node


def route_agent(state: AgentState) -> str:
    """After agent runs: tool calls pending → tools node, else END."""
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    builder.add_node("agent", unified_agent_node)
    builder.add_node("tools", make_logging_tool_node(ALL_TOOLS, "UnifiedAgent"))

    # ── Edges ──────────────────────────────────────────────────────────────────
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_agent, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")   # tool results always go back to agent

    return builder


# Uncompiled builder — chat.py calls .compile(checkpointer=...) per-request
agent_workflow = build_graph()
