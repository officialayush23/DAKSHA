# app/ai/graph.py
"""
DAKSHA Multi-Agent Graph — Supervisor Pattern
═══════════════════════════════════════════════════════════════════════
                        ┌──────────────┐
              START ───▶│  Orchestrator │◀────────────────────┐
                        └──────┬───────┘                     │
                               │ routes to                   │
              ┌────────────────┴──────────────────────────┐  │
              ▼        ▼        ▼        ▼       ▼        ▼  │
   RecommendationAgent CartAgent OfferAgent PaymentAgent  DeliveryAgent
   PostPurchaseAgent SupportAgent HumanHandoffNode         │
              │                                            │
              └──────────── all return to ────────────────▶┘
                           Orchestrator
═══════════════════════════════════════════════════════════════════════
"""
import time
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage, AIMessage
from app.ai.logging_nodes import make_logging_tool_node

from app.ai.state import AgentState
from app.ai.supervisor import supervisor_node
from app.ai.handoff import handoff_node

# ── Import all specialist agents ───────────────────────────────────────────
from app.ai.agents.recommendation_agent import (
    recommendation_agent_node,
    recommendation_tools,
)
from app.ai.agents.cart_agent import cart_agent_node, cart_tools
from app.ai.agents.offer_agent import offer_agent_node, offer_tools
from app.ai.agents.payment_agent import payment_agent_node, payment_tools
from app.ai.agents.delivery_agent import delivery_agent_node, delivery_tools
from app.ai.agents.post_purchase_agent import post_purchase_agent_node, post_purchase_tools
from app.ai.agents.support_agent import support_agent_node, support_tools


# ─────────────────────────────────────────────────────────────────────────────
# ROUTING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def route_from_orchestrator(state: AgentState) -> str:
    """After the Orchestrator runs, decide where to go next."""
    agent = state.get("current_agent", "FINISH")
    mapping = {
        "RecommendationAgent": "recommendation_tools",
        "CartAgent":           "cart_tools",
        "OfferAgent":          "offer_tools",
        "PaymentAgent":        "payment_tools",
        "DeliveryAgent":       "delivery_tools",
        "PostPurchaseAgent":   "post_purchase_tools",
        "SupportAgent":        "support_tools",
        "Handoff":             "handoff",
        "FINISH":              END,
    }
    return mapping.get(agent, END)


def route_after_tools(state: AgentState) -> str:
    """After a ToolNode runs, check if the agent wants another tool call or is done."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        # Still has pending tool calls — send back to the same agent's tool executor
        # We route by current_agent
        agent = state.get("current_agent", "")
        tool_map = {
            "RecommendationAgent": "recommendation_tools",
            "CartAgent":           "cart_tools",
            "OfferAgent":          "offer_tools",
            "PaymentAgent":         "payment_tools",
            "DeliveryAgent":       "delivery_tools",
            "PostPurchaseAgent":   "post_purchase_tools",
            "SupportAgent":        "support_tools",
        }
        return tool_map.get(agent, "orchestrator")
    return "orchestrator"


def make_agent_return_router(agent_node_fn):
    """
    Wraps an agent node so that:
    - if last message has tool_calls → go to that agent's ToolNode
    - otherwise → go back to orchestrator
    """
    def router(state: AgentState) -> str:
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return "orchestrator"
    return router


# ─────────────────────────────────────────────────────────────────────────────
# BUILD GRAPH
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    builder = StateGraph(AgentState)

    # ── Core nodes ──────────────────────────────────────────────────────────
    builder.add_node("orchestrator",  supervisor_node)
    builder.add_node("handoff",       handoff_node)

    # ── Specialist agent nodes ───────────────────────────────────────────────
    builder.add_node("recommendation_agent", recommendation_agent_node)
    builder.add_node("cart_agent",           cart_agent_node)
    builder.add_node("offer_agent",          offer_agent_node)
    builder.add_node("payment_agent",        payment_agent_node)
    builder.add_node("delivery_agent",       delivery_agent_node)
    builder.add_node("post_purchase_agent",  post_purchase_agent_node)
    builder.add_node("support_agent",        support_agent_node)

    # ── Tool executor nodes — wrapped with agent_actions logging ─────────────
    builder.add_node("recommendation_tools", make_logging_tool_node(recommendation_tools, "RecommendationAgent"))
    builder.add_node("cart_tools",           make_logging_tool_node(cart_tools,           "CartAgent"))
    builder.add_node("offer_tools",          make_logging_tool_node(offer_tools,          "OfferAgent"))
    builder.add_node("payment_tools",        make_logging_tool_node(payment_tools,        "PaymentAgent"))
    builder.add_node("delivery_tools",       make_logging_tool_node(delivery_tools,       "DeliveryAgent"))
    builder.add_node("post_purchase_tools",  make_logging_tool_node(post_purchase_tools,  "PostPurchaseAgent"))
    builder.add_node("support_tools",        make_logging_tool_node(support_tools,        "SupportAgent"))

    # ── Entry point ──────────────────────────────────────────────────────────
    builder.add_edge(START, "orchestrator")

    # ── Orchestrator → specialist agents (conditional) ──────────────────────
    builder.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "recommendation_tools": "recommendation_agent",
            "cart_tools":           "cart_agent",
            "offer_tools":          "offer_agent",
            "payment_tools":        "payment_agent",
            "delivery_tools":       "delivery_agent",
            "post_purchase_tools":  "post_purchase_agent",
            "support_tools":        "support_agent",
            "handoff":              "handoff",
            END:                    END,
        },
    )

    # ── Each agent → its ToolNode OR back to orchestrator ───────────────────
    for agent_name, tool_node_name in [
        ("recommendation_agent", "recommendation_tools"),
        ("cart_agent",           "cart_tools"),
        ("offer_agent",          "offer_tools"),
        ("payment_agent",        "payment_tools"),
        ("delivery_agent",       "delivery_tools"),
        ("post_purchase_agent",  "post_purchase_tools"),
        ("support_agent",        "support_tools"),
    ]:
        def _make_router(tool_name):
            def _router(state: AgentState) -> str:
                last = state["messages"][-1]
                if hasattr(last, "tool_calls") and last.tool_calls:
                    return tool_name
                return "orchestrator"
            return _router

        builder.add_conditional_edges(
            agent_name,
            _make_router(tool_node_name),
            {tool_node_name: tool_node_name, "orchestrator": "orchestrator"},
        )

    # ── ToolNode → back to its agent ────────────────────────────────────────
    for agent_name, tool_node_name in [
        ("recommendation_agent", "recommendation_tools"),
        ("cart_agent",           "cart_tools"),
        ("offer_agent",          "offer_tools"),
        ("payment_agent",        "payment_tools"),
        ("delivery_agent",       "delivery_tools"),
        ("post_purchase_agent",  "post_purchase_tools"),
        ("support_agent",        "support_tools"),
    ]:
        builder.add_edge(tool_node_name, agent_name)

    # ── Handoff → END (AI is paused, human takes over via WebSocket) ─────────
    builder.add_edge("handoff", END)

    return builder.compile()


# Compiled graph — imported by the chat router
agent_workflow = build_graph()
