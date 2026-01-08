# app/agents/tools.py

import json
import logging
from langchain.tools import tool
from typing import List, Optional

# 🧠 SERVICE INTEGRATIONS
from app.services.catalog_service import CatalogService
from app.services.recommendation_service import RecommendationService
from app.services.commerce_service import CommerceService
from app.services.store_service import StoreService
from app.services.human_handoff_service import HumanHandoffService
from app.services.loyalty_service import LoyaltyService
from app.services.notification_service import NotificationService
from app.services.ai_service import AIService
from app.core.database import supabase

logger = logging.getLogger("daksha.tools")

# ==============================================================================
# 🛍️ DISCOVERY & RECOMMENDATION
# ==============================================================================

@tool
def search_products_tool(query: str, limit: int = 5):
    """
    Search products using Hybrid Search (Vector + Text).
    Use for: "black shoes", "wedding dress", "running gear".
    """
    print(f"🔎 [Tool] Search: {query}")
    try:
        # 1. Try Vector (Smart)
        embedding = AIService.generate_embedding(query)
    except Exception:
        # 2. Fallback (Dumb)
        embedding = []

    try:
        results = CatalogService.search_products(query, embedding, limit)
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool
def get_personalized_recommendations_tool(user_id: str, limit: int = 5):
    """
    Get AI-curated recommendations based on user footprints.
    Use for: "What should I buy?", "Show me something new".
    """
    print(f"✨ [Tool] Personalizing for: {user_id}")
    try:
        items = RecommendationService.get_personalized_recommendations(user_id, limit)
        return json.dumps(items)
    except Exception:
        # Fallback to trending if ML pipeline fails
        return json.dumps(RecommendationService._trending_inventory(limit))

# ==============================================================================
# 📦 INVENTORY & STORES
# ==============================================================================

@tool
def find_nearest_store_tool(lat: float, lng: float):
    """Find physical stores near the user."""
    try:
        stores = StoreService.find_nearest_stores(lat, lng)
        return json.dumps(stores)
    except Exception as e:
        return f"Location error: {e}"

@tool
def check_product_availability_nearby_tool(product_variant_id: str, lat: float, lng: float):
    """
    Find which nearby store has a specific product in stock.
    Use for: "Where can I buy this today?", "Is this available nearby?"
    """
    try:
        stores = StoreService.find_nearest_stores(lat, lng, limit=5)
        results = []
        for s in stores:
            inv = (
                supabase.table("inventory")
                .select("quantity_on_hand")
                .eq("product_variant_id", product_variant_id)
                .eq("fulfillment_location_id", s["fulfillment_location_id"])
                .maybe_single()
                .execute()
            ).data
            if inv and inv["quantity_on_hand"] > 0:
                s["qty"] = inv["quantity_on_hand"]
                results.append(s)
        
        return json.dumps(results) if results else "Out of stock in nearby stores."
    except Exception as e:
        return f"Stock check failed: {e}"

# ==============================================================================
# 🛒 COMMERCE (CART & CHECKOUT)
# ==============================================================================

@tool
def get_cart_tool(user_id: str):
    """Fetch the user's active shopping cart items."""
    if user_id == "guest": 
        return "Please log in to view cart."
    try:
        # Use CommerceService for consistency
        cart_snapshot = CommerceService.get_cart_snapshot(user_id)
        if not cart_snapshot or not cart_snapshot.get("items"):
            return "Cart is empty."
        return json.dumps({
            "cart_id": cart_snapshot["cart"]["id"],
            "items": cart_snapshot["items"],
            "item_count": len(cart_snapshot["items"])
        })
    except Exception as e:
        return f"Cart error: {e}"

@tool
def add_to_cart_tool(user_id: str, variant_id: str, quantity: int = 1, fulfillment_location_id: str = None):
    """Add an item to the cart."""
    if user_id == "guest": 
        return "Login required."
    try:
        # Use CommerceService for consistency
        result = CommerceService.add_item(
            user_id=user_id,
            variant_id=variant_id,
            qty=quantity,
            fulfillment_location_id=fulfillment_location_id or ""
        )
        return f"Added {quantity} item(s) to cart."
    except Exception as e:
        return f"Failed to add: {e}"

@tool
def get_user_context_tool(user_id: str):
    """
    Fetch addresses and payment methods for checkout context.
    ALWAYS call this before checkout_tool.
    """
    if user_id == "guest": return "Guest"
    try:
        addrs = supabase.table("user_addresses").select("*").eq("user_id", user_id).execute().data
        cards = supabase.table("user_payment_methods").select("id, card_last4, card_brand").eq("user_id", user_id).execute().data
        return json.dumps({"addresses": addrs, "cards": cards})
    except: return "{}"

@tool
def checkout_tool(user_id: str, address_id: str = None, order_type: str = "delivery"):
    """
    Create an order from the cart.
    Requires user confirmation of address_id first.
    """
    if user_id == "guest":
        return "Login required to checkout."
    try:
        res = CommerceService.checkout_commit(
            user_id=user_id,
            order_type=order_type,
            pickup_location_id=None,
            address_id=address_id,
            promotion_code=None
        )
        return json.dumps({
            "success": True, 
            "order_id": res["order_id"], 
            "total": res["total"]
        })
    except Exception as e:
        return f"Checkout Failed: {e}"

# ==============================================================================
# 📋 ORDERS & SUPPORT
# ==============================================================================

@tool
def get_order_history_tool(user_id: str, limit: int = 5):
    """
    Fetch past orders for the user.
    Use for: "Show my orders", "What did I buy last?"
    """
    if user_id == "guest": return "Login to see orders."
    try:
        res = supabase.table("orders").select("id, status, total_amount, created_at, order_items(count)").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return json.dumps(res.data)
    except Exception as e:
        return f"History error: {e}"

@tool
def track_order_tool(order_id: str):
    """Get specific order status."""
    try:
        res = supabase.table("orders").select("status, total_amount, created_at").eq("id", order_id).single().execute()
        return json.dumps(res.data) if res.data else "Order not found."
    except: return "Order not found."

@tool
def lodge_complaint_tool(user_id: str, issue: str, description: str):
    """
    Lodge a formal complaint or return request.
    Triggers Human Handoff immediately.
    """
    try:
        # Create Ticket
        HumanHandoffService.trigger(
            session_id=None,
            user_id=user_id,
            reason=issue,
            summary=description
        )
        return "Complaint lodged. A human agent will review this shortly."
    except Exception as e:
        return f"Failed to lodge complaint: {e}"

@tool
def handoff_to_human_tool(user_id: str, reason: str, summary: str):
    """
    Escalate the conversation to a human agent.
    Use when the user is angry, confused, or asks for a human.
    """
    try:
        HumanHandoffService.trigger(
            session_id=None,
            user_id=user_id, 
            reason=reason, 
            summary=summary
        )
        return "I have notified a human agent. They will take over shortly."
    except: return "Handoff failed."

@tool
def check_loyalty_tool(user_id: str):
    """Check loyalty points and available rewards."""
    try:
        summary = LoyaltyService.get_loyalty_summary(user_id)
        return json.dumps(summary) if summary else "No loyalty data."
    except: return "Loyalty check failed."