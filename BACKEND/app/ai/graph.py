# app/ai/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.ai.state import AgentState
from app.ai.supervisor import supervisor_node
from app.ai.handoff import handoff_node

# Import Agents and Tools
from app.ai.agents.recommendation_agent import recommendation_agent_node, rec_tools
from app.ai.agents.checkout_agent import checkout_agent_node, checkout_tools
from app.ai.agents.support_agent import support_agent_node, support_tools
from app.ai.agents.loyalty_agent import loyalty_agent_node, loyalty_tools
from app.ai.agents.inventory_agent import inventory_agent_node, inventory_tools

def build_graph():
    builder = StateGraph(AgentState)

    # Add Core Nodes
    builder.add_node("Supervisor", supervisor_node)
    builder.add_node("Handoff", handoff_node)

    # Add Worker Nodes
    builder.add_node("RecommendationAgent", recommendation_agent_node)
    builder.add_node("CheckoutAgent", checkout_agent_node)
    builder.add_node("SupportAgent", support_agent_node)
    builder.add_node("LoyaltyAgent", loyalty_agent_node)
    builder.add_node("InventoryAgent", inventory_agent_node)

    # Add Tool Nodes
    builder.add_node("RecommendationTools", ToolNode(rec_tools))
    builder.add_node("CheckoutTools", ToolNode(checkout_tools))
    builder.add_node("SupportTools", ToolNode(support_tools))
    builder.add_node("LoyaltyTools", ToolNode(loyalty_tools))
    builder.add_node("InventoryTools", ToolNode(inventory_tools))
    
    # ==========================
    # EDGES & ROUTING
    # ==========================
    builder.add_edge(START, "Supervisor")

    builder.add_conditional_edges(
        "Supervisor",
        lambda state: state.get("current_agent", "FINISH"),
        {
            "RecommendationAgent": "RecommendationAgent",
            "CheckoutAgent": "CheckoutAgent",
            "SupportAgent": "SupportAgent",
            "LoyaltyAgent": "LoyaltyAgent",
            "InventoryAgent": "InventoryAgent",
            "Handoff": "Handoff",
            "FINISH": END
        }
    )

    # Worker Loops
    workers = ["Recommendation", "Checkout", "Support", "Loyalty", "Inventory"]
    for prefix in workers:
        agent_name = f"{prefix}Agent"
        tool_name = f"{prefix}Tools"
        
        # If the LLM called a tool, go to tools. Otherwise, return to Supervisor.
        builder.add_conditional_edges(
            agent_name,
            lambda state, t=tool_name: t if getattr(state["messages"][-1], "tool_calls", None) else "Supervisor"
        )
        # Tools always return to Supervisor
        builder.add_edge(tool_name, "Supervisor")

    builder.add_edge("Handoff", END)

    return builder.compile()

agent_workflow = build_graph()