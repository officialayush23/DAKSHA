# app/ai/tools/checkout_tools.py
import uuid
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.cart_service import add_item_to_cart, remove_item_from_cart, update_cart_item_quantity, get_hydrated_cart
from app.services.checkout_service import create_checkout_after_fulfillment, finalize_checkout
from app.enums.db_enums import ChannelEnum, FulfillmentTypeEnum

@tool
def add_to_cart(user_id: str, session_id: str, variant_id: str, quantity: int) -> str:
    """Adds a specific product variant to the user's cart."""
    with SessionLocal() as db:
        try:
            add_item_to_cart(db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), product_variant_id=uuid.UUID(variant_id), quantity=quantity, channel=ChannelEnum.web, source="agent_action")
            return f"Successfully added {quantity} item(s) to the cart."
        except Exception as e:
            return f"Failed to add to cart: {str(e)}"

@tool
def update_cart_quantity(user_id: str, session_id: str, variant_id: str, quantity: int) -> str:
    """Updates the quantity of an item already in the cart. Set quantity to 0 to remove."""
    with SessionLocal() as db:
        try:
            update_cart_item_quantity(db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), product_variant_id=uuid.UUID(variant_id), new_quantity=quantity, channel=ChannelEnum.web, source="agent_action")
            return f"Cart updated. New quantity: {quantity}."
        except Exception as e:
            return f"Failed to update cart: {str(e)}"

@tool
def view_cart(user_id: str) -> str:
    """Gets the current contents of the user's cart."""
    with SessionLocal() as db:
        try:
            cart_data = get_hydrated_cart(db, user_id=uuid.UUID(user_id))
            return f"Cart contents: {cart_data}"
        except Exception as e:
            return f"Error fetching cart: {str(e)}"

@tool
def start_checkout(user_id: str, session_id: str, cart_id: str, fulfillment_type: str, store_id: str = None) -> str:
    """Initiates checkout and locks inventory. fulfillment_type must be 'delivery' or 'pickup'."""
    with SessionLocal() as db:
        try:
            f_type = FulfillmentTypeEnum(fulfillment_type)
            s_id = uuid.UUID(store_id) if store_id else None
            checkout = create_checkout_after_fulfillment(db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), cart_id=uuid.UUID(cart_id), fulfillment_type=f_type, store_id=s_id)
            return f"Checkout started successfully. Checkout ID: {checkout.id}."
        except Exception as e:
            return f"Failed to start checkout: {str(e)}"
        
        
        
        
# need to add the remove from cart , finalize checkout and apply coupon code tools as well, get coupons too , basically all the things the router of checkout does and cart does , but int tools: