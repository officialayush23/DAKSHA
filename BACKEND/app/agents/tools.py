from langchain.tools import tool
from typing import Optional, List
from app.services.commerce_service import CommerceService
from app.services.ai_service import AIService
from app.services.user_service import UserService
from app.services.support_service import SupportService
from app.services.recommendation_service import RecommendationService
from app.services.loyalty_service import LoyaltyService
from app.services.payment_service import PaymentService

# --- 1. Recommendation Agent Tools ---
@tool
def search_products_tool(query: str):
    """Search for products using hybrid search (text + semantic)."""
    vector = AIService.generate_embedding(query)
    # Using specific limit for recommendations
    res = CommerceService.search_hybrid(query, vector, limit=5)
    return res.data

@tool
def get_personalized_recommendations_tool(user_id: str):
    """Get product suggestions based on user footprint/history."""
    return RecommendationService.get_personalized_recommendations(user_id)

@tool
def get_active_campaigns_tool(user_id: str):
    """Get active ads and promotional campaigns."""
    return RecommendationService.get_active_campaigns(user_id)

# --- 2. Inventory Agent Tools ---
@tool
def check_stock_tool(sku: str, store_id: str):
    """Check real-time stock availability at a specific store."""
    return CommerceService.get_stock(sku, store_id)

@tool
def find_nearest_store_tool(lat: float, long: float):
    """Find the nearest store with inventory."""
    # Mocking location logic for now, in prod use PostGIS
    return [{"store_id": "store_pune_01", "name": "Phoenix Mall", "distance": "2km"}]

# --- 3. Payment & Fulfillment Agent Tools ---
@tool
async def add_to_cart_tool(user_id: str, variant_id: str, store_id: str, quantity: int = 1):
    """Add item to cart and reserve stock."""
    return await CommerceService.add_to_cart(user_id, variant_id, store_id, quantity)

@tool
async def checkout_tool(user_id: str, address_id: str, payment_method_id: str, order_type: str):
    """Process checkout and payment."""
    return await PaymentService.process_checkout(user_id, address_id, payment_method_id, order_type)

# --- 4. Loyalty Agent Tools ---
@tool
def check_loyalty_status_tool(user_id: str):
    """Check points balance and eligible rewards."""
    return LoyaltyService.get_loyalty_summary(user_id)

# --- 5. Post-Purchase Support Tools ---
@tool
async def create_ticket_tool(user_id: str, issue: str, summary: str, sentiment: float, order_id: str = None):
    """Create a support ticket for human resolution."""
    return await SupportService.create_ticket(user_id, issue, summary, sentiment, order_id)

@tool
async def track_order_tool(order_id: str):
    """Get shipping status of an order."""
    # Connecting to the Order History logic
    return {"status": "Out for Delivery", "location": "Near FC Road"} # Mocked for speed