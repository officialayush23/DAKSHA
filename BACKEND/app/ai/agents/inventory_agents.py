# app/ai/agents/inventory_agents.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.state import AgentState
from app.ai.rules.inventory_rules import INVENTORY_AGENT_PROMPT
from app.ai.tools.inventory_tools import check_item_stock, find_nearest_pickup_stores, agent_reschedule_delivery

inventory_tools = [check_item_stock, find_nearest_pickup_stores, agent_reschedule_delivery]
llm_with_tools = get_llm().bind_tools(inventory_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", INVENTORY_AGENT_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain = prompt | llm_with_tools

def inventory_agent_node(state: AgentState):
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "current_agent": "InventoryAgent"}