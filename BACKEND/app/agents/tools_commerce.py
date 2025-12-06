from langchain.tools import tool
from app.services.commerce_service import CommerceService
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService


@tool
def search_products_tool(query: str, limit: int = 6) -> list:
    """
    Search for products using hybrid search on name/description/style.
    """
    embedding = AIService.generate_embedding(query)
    return CatalogService.search_products(query, embedding, limit)


@tool
async def add_to_cart_tool(user_id: str, variant_id: str, store_id: str, quantity: int = 1) -> dict:
    """
    Reserve inventory with optimistic locking and add to cart.
    """
    return await CommerceService.add_to_cart(user_id, variant_id, store_id, quantity)
