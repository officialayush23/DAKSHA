# app/ai/agents/cart_agent.py
"""
CartAgent — Groq llama-3.3-70b
Handles all cart CRUD: add, remove, update, view, clear.
Checks stock before adding. Wraps existing checkout_tools.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm_for_agent
from app.ai.state import AgentState
from app.ai.policy.company_policy import build_agent_prompt
from app.ai.tools.checkout_tools import (
    view_cart, add_to_cart, update_cart_quantity, remove_from_cart,
)
from app.ai.tools.inventory_tools import check_item_stock

CART_INSTRUCTIONS = """
You manage the user's shopping cart. You can:
  • view_cart — show what's in the cart
  • add_to_cart — add a product variant by ID and quantity
  • update_cart_quantity — change quantity of an existing cart item
  • remove_from_cart — remove an item completely
  • check_item_stock — verify stock BEFORE adding to cart

RULES:
1. ALWAYS call check_item_stock before add_to_cart. If out of stock, tell the user and stop.
2. After any cart mutation, call view_cart once to show the updated cart.
3. Wrap the view_cart result in <UI_DATA> ... </UI_DATA> tags so the UI can render it.
4. If the user wants to checkout or pay, tell them to say "I want to checkout" —
   that will route to the PaymentAgent. Never call checkout tools yourself.
5. Be concise. Confirm actions in one sentence, then show the cart.

Current user ID: {user_id}
Current session ID: {session_id}
Order mode: {order_mode}
"""

cart_tools = [view_cart, add_to_cart, update_cart_quantity, remove_from_cart, check_item_stock]

_llm = get_llm_for_agent("CartAgent").bind_tools(cart_tools)
_llm_text = get_llm_for_agent("CartAgent")   # no tools for post-tool response

_prompt = ChatPromptTemplate.from_messages([
    ("system", build_agent_prompt("Cart Agent", CART_INSTRUCTIONS)),
    MessagesPlaceholder(variable_name="messages"),
])

_chain = _prompt | _llm
_chain_text = _prompt | _llm_text


def cart_agent_node(state: AgentState) -> dict:
    from langchain_core.messages import ToolMessage
    messages = state["messages"]
    ctx = {
        "messages": messages,
        "user_id": state.get("user_id", ""),
        "session_id": state.get("session_id", ""),
        "order_mode": state.get("order_mode", "online"),
    }
    # Anti-loop: force text reply after tool result
    if messages and isinstance(messages[-1], ToolMessage):
        response = _chain_text.invoke(ctx)
    else:
        response = _chain.invoke(ctx)
    return {"messages": [response], "current_agent": "CartAgent"}
