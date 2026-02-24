# app/ai/agents/recommendation_agent.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.state import AgentState
from app.ai.tools.recommendation_tools import find_similar_by_image, recommend_products, search_for_items

# You would define this in rules/recommendation_rules.py
RECOMMENDATION_PROMPT = "You are the Recommendation Agent. Help the user find the perfect products."

tools = [recommend_products, search_for_items, find_similar_by_image]
llm_with_tools = get_llm().bind_tools(tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", RECOMMENDATION_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain = prompt | llm_with_tools

def recommendation_agent_node(state: AgentState):
    """Executes the recommendation agent logic."""
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "current_agent": "RecommendationAgent"}