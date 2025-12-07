from typing import Optional

from langchain.tools import tool
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService
from app.services.commerce_service import CommerceService
from app.services.loyalty_service import LoyaltyService
from app.services.recommendation_service import RecommendationService
from app.services.support_service import SupportService
from app.services.user_service import UserService
from app.services.payment_service import PaymentService
from app.services.store_service import StoreService
from app.services.notification_service import NotificationService
from app.database import supabase


# ===============================
# 1. RECOMMENDATION / CATALOG
# ===============================


@tool
def search_products_tool(query: str, limit: int = 6) -> list:
    """
    Search for products using hybrid search (text + semantic) on the products table.
    """
    embedding = AIService.generate_embedding(query)
    return CatalogService.search_products(query, embedding, limit)


@tool
def get_personalized_recommendations_tool(user_id: str, limit: int = 6) -> list:
    """
    Suggest products based on user browsing history (user_footprints).
    """
    return RecommendationService.get_personalized_recommendations(user_id, limit)


@tool
def get_active_campaigns_tool(user_id: str) -> list:
    """
    Fetch active ad campaigns / special collections.
    Currently not deeply personalized, just returns active campaigns.
    """
    return RecommendationService.get_active_campaigns(user_id)


# ===============================
# 2. INVENTORY / STORES
# ===============================


@tool
def check_stock_tool(sku: str, store_id: str):
    """
    Check real-time stock availability and display_location for a SKU at a store.
    Returns quantity_on_hand, reserved, aisle/bay/shelf, section_id, etc.
    """
    return CommerceService.get_stock_by_sku(sku, store_id)

@tool
def find_nearest_store_tool(lat: float, long: float, limit: int = 5):
    """
    Find nearest stores to a given lat/long using the Postgres PostGIS function
    find_nearest_stores(). Distance is computed in the DB, not Python.
    """
    stores = StoreService.find_nearest_stores(lat=lat, lng=long, limit=limit)
    return [
        {
            "store_id": s["id"],
            "store_code": s["store_code"],
            "name": s["name"],
            "city": s["city"],
            "distance_meters": s["distance_meters"],
        }
        for s in (stores or [])
    ]

# ===============================
# 3. CART & CHECKOUT
# ===============================


@tool
async def add_to_cart_tool(
    user_id: str,
    variant_id: str,
    store_id: str,
    quantity: int = 1,
):
    """
    Reserve stock with optimistic locking and add to user's cart.
    """
    return await CommerceService.add_to_cart(user_id, variant_id, store_id, quantity)


@tool
async def checkout_tool(
    user_id: str,
    order_type: str,
    store_id: Optional[str] = None,
    address_id: Optional[str] = None,
    promotion_code: Optional[str] = None,
):
    """
    Create an order from the cart and compute discounts; does NOT confirm payment.
    Payment confirmation is handled via PaymentService.
    """
    return CommerceService.checkout(
        user_id=user_id,
        order_type=order_type,
        store_id=store_id,
        address_id=address_id,
        promotion_code=promotion_code,
    )


# ===============================
# 4. LOYALTY
# ===============================


@tool
def check_loyalty_status_tool(user_id: str):
    """
    Check the user's loyalty points balance and available reward offers.
    Use when user asks "How many points do I have?" or "Any rewards?"
    """
    return LoyaltyService.get_loyalty_summary(user_id)


# ===============================
# 5. SUPPORT / ORDERS
# ===============================


@tool
async def create_support_ticket_tool(
    user_id: str,
    issue_summary: str,
    conversation_summary: str,
    sentiment_score: float,
    order_id: Optional[str] = None,
):
    """
    Create a support ticket and publish to support dashboard channel.
    """
    ticket = await SupportService.create_ticket(
        user_id=user_id,
        issue=issue_summary,
        summary=conversation_summary,
        sentiment=sentiment_score,
        order_id=order_id,
    )
    return ticket


@tool
def track_order_tool(order_id: str):
    """
    Return basic order status for tracking (status + latest fulfillment).
    """
    return CommerceService.track_order(order_id)


# ===============================
# 6. USER PROFILE
# ===============================


@tool
async def update_user_profile_tool(user_id: str, field: str, value: str) -> str:
    """
    Update a user profile field (full_name, phone_number, gender, date_of_birth).
    NOTE: `gender` here is user.gender (varchar), NOT the product gender_enum.
    """
    valid = {"full_name", "phone_number", "gender", "date_of_birth"}
    if field not in valid:
        return f"Error: Cannot update field '{field}'."

    try:
        await UserService.update_profile(user_id, {field: value})
        return f"Successfully updated {field}."
    except Exception as e:
        return f"Update failed: {str(e)}"


# ===============================
# 7. NOTIFICATIONS
# ===============================


@tool
async def send_notification_tool(
    user_id: str,
    title: str,
    body: str,
    type: str = "info",
) -> str:
    """
    Sends an in-app notification to the user and pushes via WebSocket.
    Use when you want to proactively confirm actions (order placed, coupon applied, etc.).
    """
    record = await NotificationService.send_to_user(user_id, title, body, type)
    return f"Notification sent with id={record['id']}"


# ===============================
# 8. FULFILLMENT (DELIVERY / PICKUP)
# ===============================


@tool
def schedule_fulfillment_tool(
    order_id: str,
    fulfillment_type: str = "delivery",   # 'delivery' | 'pickup' | 'reservation'
    scheduled_for: Optional[str] = None,  # ISO datetime string
    location_note: Optional[str] = None,
) -> dict:
    """
    Schedule fulfillment for an order. Use this when user chooses delivery/pickup time & location.

    - fulfillment_type: 'delivery', 'pickup', or 'reservation'
    - scheduled_for: optional datetime string
    - location_note: note like "Store #23 - Pickup Counter"
    """
    res = (
        supabase.table("orders")
        .select("id, user_id, status")
        .eq("id", order_id)
        .single()
        .execute()
    )
    if not res.data:
        return {"error": "Order not found"}

    # You can add status checks here (only 'paid' should be schedulable, etc.)
    payload = {
        "order_id": order_id,
        "status": "scheduled",
        "fulfillment_type": fulfillment_type,
        "scheduled_for": scheduled_for,
        "location_note": location_note,
    }

    created = supabase.table("fulfillments").insert(payload).execute()
    return created.data[0]


@tool
def get_fulfillment_status_tool(order_id: str) -> dict:
    """
    Check fulfillment status for a given order.
    Use when user asks 'Where is my order?' or 'Is my pickup ready?'
    """
    res = (
        supabase.table("fulfillments")
        .select("*")
        .eq("order_id", order_id)
        .order("shipped_at", desc=True)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return {"status": "not_scheduled"}
    return res.data
