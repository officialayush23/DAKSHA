# app/ai/agents/checkout_agent.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.ai.llm import get_llm
from app.ai.state import AgentState
from app.ai.rules.checkout_rules import CHECKOUT_AGENT_PROMPT
from app.ai.tools.checkout_tools import (
    view_cart, 
    add_to_cart, 
    update_cart_quantity, 
    remove_from_cart,
    start_delivery_checkout, 
    find_pickup_stores, 
    start_pickup_checkout, 
    get_checkout_addresses, 
    get_checkout_coupons, 
    apply_coupon_code, 
    finalize_payment
)

checkout_tools = [
    view_cart, 
    add_to_cart, 
    update_cart_quantity, 
    remove_from_cart,
    start_delivery_checkout, 
    find_pickup_stores, 
    start_pickup_checkout, 
    get_checkout_addresses, 
    get_checkout_coupons, 
    apply_coupon_code, 
    finalize_payment
]

llm_with_tools = get_llm().bind_tools(checkout_tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", CHECKOUT_AGENT_PROMPT),
    MessagesPlaceholder(variable_name="messages")
])

chain = prompt | llm_with_tools

def checkout_agent_node(state: AgentState):
    # Inject user/session info so the prompt template can format it
    response = chain.invoke({
        "messages": state["messages"], 
        "user_id": state["user_id"],
        "session_id": state["session_id"],
        "user_summary": state.get("user_summary", "None")
    })
    return {"messages": [response], "current_agent": "CheckoutAgent"}