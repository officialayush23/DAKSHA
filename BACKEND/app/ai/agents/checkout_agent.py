# app/ai/agents/checkout_agent.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.state import AgentState
from app.ai.rules.checkout_rules import CHECKOUT_AGENT_PROMPT
from app.ai.tools.checkout_tools import add_to_cart, update_cart_quantity, view_cart, start_checkout

checkout_tools = [add_to_cart, update_cart_quantity, view_cart, start_checkout]
llm_with_tools = get_llm().bind_tools(checkout_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", CHECKOUT_AGENT_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain = prompt | llm_with_tools

def checkout_agent_node(state: AgentState):
    response = chain.invoke({"messages": state["messages"], "user_summary": state.get("user_summary", "")})
    return {"messages": [response], "current_agent": "CheckoutAgent"}