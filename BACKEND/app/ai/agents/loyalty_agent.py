# app/ai/agents/loyalty_agent.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.state import AgentState
from app.ai.rules.discount_rules import LOYALTY_AGENT_PROMPT
from app.ai.tools.loyalty_tools import get_loyalty_balance, apply_discount_code

loyalty_tools = [get_loyalty_balance, apply_discount_code]
llm_with_tools = get_llm().bind_tools(loyalty_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", LOYALTY_AGENT_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain = prompt | llm_with_tools

def loyalty_agent_node(state: AgentState):
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "current_agent": "LoyaltyAgent"}