# app/ai/agents/recommendation_agent.py
"""
RecommendationAgent — Gemini 2.5 Flash
Handles: semantic search, personalised recs, image-based search, trending,
and conversational recs (multi-turn clarification → search).
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, ToolMessage
from app.ai.llm import get_llm_for_agent
from app.ai.state import AgentState
from app.ai.policy.company_policy import build_agent_prompt
from app.ai.tools.recommendation_tools import (
    find_similar_by_image,
    recommend_products,
    search_for_items,
    get_trending_products,
)

MAX_CLARIFICATION_TURNS = 3  # ask at most 3 guided questions before searching

REC_INSTRUCTIONS = """
You help users discover fashion products at DAKSHA.

CAPABILITIES:
  • search_for_items        — semantic search (use for: "red dress", "casual shirt under ₹1000")
  • recommend_products      — personalised recommendations based on user history
  • find_similar_by_image   — find products visually similar to an uploaded photo
  • get_trending_products   — show what's trending (by category, brand, or globally)

DECISION TREE:
  User uploads image             → find_similar_by_image
  User asks "what's trending"    → get_trending_products
  User has vague/occasion query  → CONVERSATIONAL CLARIFICATION (see below)
  Specific product preference    → search_for_items
  "Recommend something for me"   → recommend_products

CONVERSATIONAL CLARIFICATION MODE:
When the user has a vague query (e.g. "I'm going to a wedding", "suggest outfit for party"):
  1. Ask ONE focused clarifying question per turn. Examples:
     - "What's the occasion — formal wedding, cocktail, or festive?"
     - "Any preference on budget? Under ₹1000, ₹1000-3000, or above ₹3000?"
     - "What size are you and do you prefer traditional or western wear?"
  2. Accumulate answers across turns (they are in clarification_context).
  3. After {max_clarification_turns} turns OR when you have enough info, call search_for_items.
  4. NEVER ask more than {max_clarification_turns} questions — search with what you have.

RULES:
1. One tool call per turn.
2. Always wrap product results in <UI_DATA> ... </UI_DATA> tags.
3. For image search: the image embedding is handled — just call find_similar_by_image with session_id.
4. If zero results returned, ask the user to broaden their search.
5. After showing results, offer: "Want me to add any of these to your cart?"

User ID: {user_id}
Session ID: {session_id}
Clarification context so far: {clarification_context}
Clarification turns used: {clarification_turn}/{max_clarification_turns}
"""

recommendation_tools = [
    recommend_products,
    search_for_items,
    find_similar_by_image,
    get_trending_products,
]

_llm = get_llm_for_agent("RecommendationAgent").bind_tools(recommendation_tools)
_llm_text = get_llm_for_agent("RecommendationAgent")

_prompt = ChatPromptTemplate.from_messages([
    ("system", build_agent_prompt("Recommendation Agent", REC_INSTRUCTIONS)),
    MessagesPlaceholder(variable_name="messages"),
])

_chain = _prompt | _llm
_chain_text = _prompt | _llm_text


def recommendation_agent_node(state: AgentState) -> dict:
    messages = state["messages"]
    clarification_turn = state.get("clarification_turn", 0)
    clarification_context = state.get("clarification_context", {})

    ctx = {
        "messages": messages,
        "user_id": state.get("user_id", ""),
        "session_id": state.get("session_id", ""),
        "clarification_context": clarification_context,
        "clarification_turn": clarification_turn,
        "max_clarification_turns": MAX_CLARIFICATION_TURNS,
    }

    # Anti-loop: force text reply after tool result
    if messages and isinstance(messages[-1], ToolMessage):
        response = _chain_text.invoke(ctx)
        # Reset clarification context after a successful search
        return {
            "messages": [response],
            "current_agent": "RecommendationAgent",
            "clarification_turn": 0,
            "clarification_context": {},
        }

    response = _chain.invoke(ctx)

    # If no tool call was made, this was a clarifying question — increment turn counter
    updates: dict = {"messages": [response], "current_agent": "RecommendationAgent"}
    if not (hasattr(response, "tool_calls") and response.tool_calls):
        updates["clarification_turn"] = clarification_turn + 1

    return updates