# app/ai/agents/support_agent.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.state import AgentState
from app.ai.rules.support_rules import SUPPORT_AGENT_PROMPT
from app.ai.tools.support_tools import process_return, process_exchange, create_complaint

support_tools = [process_return, process_exchange, create_complaint]
llm_with_tools = get_llm().bind_tools(support_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", SUPPORT_AGENT_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain = prompt | llm_with_tools

def support_agent_node(state: AgentState):
    response = chain.invoke({"messages": state["messages"], "user_summary": state.get("user_summary", "")})
    return {"messages": [response], "current_agent": "SupportAgent"}