import uuid
import json
from datetime import datetime, timezone
from langchain.tools import tool
from app.core.database import SessionLocal
from app.enums.db_enums import FulfillmentTypeEnum, ChannelEnum

from app.services.cart_service import (
    get_hydrated_cart, add_item_to_cart, update_cart_item_quantity, remove_item_from_cart
)
from app.services.checkout_service import create_checkout_after_fulfillment, finalize_checkout
from app.services.store_availability_service import get_nearest_stores_with_cart
from app.models.models import AgentEvent

def log_agent_event(db, order_id, agent_name, event_type, payload):
    db.add(AgentEvent(order_id=order_id, agent_name=agent_name, event_type=event_type, payload=payload))
    db.commit()

@tool
def view_cart(user_id: str) -> str:
    """Gets the current contents of the user's cart."""
    with SessionLocal() as db:
        try:
            data = get_hydrated_cart(db, user_id=uuid.UUID(user_id))
            return json.dumps(data)
        except Exception as e:
            return f"Error fetching cart: {str(e)}"

@tool
def add_to_cart(user_id: str, session_id: str, variant_id: str, quantity: int) -> str:
    """Adds a specific product variant to the user's cart."""
    with SessionLocal() as db:
        try:
            add_item_to_cart(
                db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), 
                product_variant_id=uuid.UUID(variant_id), quantity=quantity, 
                channel=ChannelEnum.web, source="agent_action"
            )
            return f"Successfully added {quantity} item(s) to the cart."
        except Exception as e:
            return f"Failed to add to cart: {str(e)}"

@tool
def update_cart_quantity(user_id: str, session_id: str, variant_id: str, quantity: int) -> str:
    """Updates the quantity of an item already in the cart."""
    with SessionLocal() as db:
        try:
            update_cart_item_quantity(
                db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), 
                product_variant_id=uuid.UUID(variant_id), new_quantity=quantity, 
                channel=ChannelEnum.web, source="agent_action"
            )
            return f"Cart updated. New quantity: {quantity}."
        except Exception as e:
            return f"Failed to update cart: {str(e)}"

@tool
def remove_from_cart(user_id: str, session_id: str, variant_id: str) -> str:
    """Removes an item completely from the cart."""
    with SessionLocal() as db:
        try:
            success = remove_item_from_cart(
                db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), 
                product_variant_id=uuid.UUID(variant_id), channel=ChannelEnum.web, source="agent_action"
            )
            return "Item removed from cart successfully." if success else "Item not found in cart."
        except Exception as e:
            return f"Failed to remove from cart: {str(e)}"

@tool
def start_delivery_checkout(user_id: str, session_id: str, cart_id: str) -> str:
    """Initiates delivery checkout and locks inventory."""
    with SessionLocal() as db:
        try:
            checkout = create_checkout_after_fulfillment(
                db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), 
                cart_id=uuid.UUID(cart_id), fulfillment_type=FulfillmentTypeEnum.delivery
            )
            return json.dumps({"checkout_id": str(checkout.id), "locked_price": float(checkout.locked_price)})
        except Exception as e:
            return f"Error starting delivery checkout: {str(e)}"

@tool
def start_pickup_checkout(user_id: str, session_id: str, cart_id: str, store_id: str) -> str:
    """Initiates pickup checkout."""
    with SessionLocal() as db:
        try:
            checkout = create_checkout_after_fulfillment(
                db=db, user_id=uuid.UUID(user_id), session_id=uuid.UUID(session_id), 
                cart_id=uuid.UUID(cart_id), fulfillment_type=FulfillmentTypeEnum.pickup, store_id=uuid.UUID(store_id)
            )
            return json.dumps({"checkout_id": str(checkout.id), "locked_price": float(checkout.locked_price)})
        except Exception as e:
            return f"Error starting pickup checkout: {str(e)}"

@tool
async def finalize_payment(checkout_id: str, address_id: str = None, scheduled_time: str = None, points: int = 0) -> str:
    """Finalizes the order. Call this to actually place the order!"""
    db = SessionLocal()
    try:
        dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00')) if scheduled_time else None
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        result = await finalize_checkout(
            db=db, checkout_id=uuid.UUID(checkout_id), 
            delivery_address_id=uuid.UUID(address_id) if address_id else None,
            scheduled_time=dt, redeem_loyalty_points=points
        )
        
        if result.get("order_id"):
            log_agent_event(db, result["order_id"], "UnifiedAgent", "finalize_payment", result)
            
        return json.dumps(result)
    except Exception as e:
        return f"Error finalizing: {str(e)}"
    finally:
        db.close()