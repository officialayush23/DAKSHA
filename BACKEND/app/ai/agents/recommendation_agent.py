# app/ai/agents/recommendation_agent.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.state import AgentState
from app.ai.tools.recommendation_tools import find_similar_by_image, recommend_products, search_for_items

RECOMMENDATION_PROMPT = """You are the Recommendation Agent. Help the user find products.

CRITICAL RULES:
1. ONLY call ONE tool per user request. Do not call multiple tools.
2. If the user provides a general preference (e.g. "I want red shirts"), use `search_for_items`.
3. If the user asks for personalized recommendations, use `recommend_products`.
4. After you receive the tool's output, immediately summarize the results for the user and stop.
5. If the tool returns no results, apologize and ask them to clarify.
6. don't overthink it.
"""

rec_tools = [recommend_products, search_for_items, find_similar_by_image]

# Note: We keep the temperature low to prevent hallucinated tool calls
llm_with_tools = get_llm().bind_tools(rec_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", RECOMMENDATION_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain = prompt | llm_with_tools

def recommendation_agent_node(state: AgentState):
    """Executes the recommendation agent logic."""
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "current_agent": "RecommendationAgent"}