# app/ai/tools/inventory_tools.py
import uuid
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.admin_global_service import get_inventory_overview_service
from app.services.store_availability_service import get_nearest_stores_with_cart
from app.services.fulfillment_agent_service import reschedule_delivery

@tool
def check_item_stock(variant_id: str, store_id: str = None) -> str:
    """Checks global warehouse and optional store stock for a product variant."""
    with SessionLocal() as db:
        try:
            data = get_inventory_overview_service(db, uuid.UUID(variant_id), uuid.UUID(store_id) if store_id else None)
            return f"Stock Data: {data}"
        except Exception as e:
            return f"Error checking stock: {str(e)}"

@tool
def find_nearest_pickup_stores(cart_id: str, lat: float, lng: float) -> str:
    """Finds stores near the user that have the ENTIRE cart in stock."""
    with SessionLocal() as db:
        try:
            stores = get_nearest_stores_with_cart(db, uuid.UUID(cart_id), lat, lng)
            return f"Available stores: {stores}"
        except Exception as e:
            return f"Error finding stores: {str(e)}"

@tool
def agent_reschedule_delivery(order_id: str, new_address: str = None) -> str:
    """Reschedules a failed delivery attempt."""
    with SessionLocal() as db:
        try:
            # Note: This is an async function in your backend, but tools are synchronous by default in LangChain 
            # unless using @tool(is_async=True). For now, we will handle the synchronous block:
            import asyncio
            result = asyncio.run(reschedule_delivery(db, uuid.UUID(order_id), new_address))
            return f"Reschedule result: {result}"
        except Exception as e:
            return f"Error rescheduling: {str(e)}"
        
        
# inventory agent should only answer things like , if this specific item is in stock at this store, or which nearby stores have all items in the cart, rescheduling and all are fulfillment and postpurchase agent jobs, so we can move the rescheduling tool to fulfillment agent tools and the prompt rules should reflect that.