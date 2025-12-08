from fastapi import APIRouter
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/products", tags=["Catalog"])


@router.get("")
async def get_products(category: str = None, brand: str = None, sort: str = "newest"):
    products = CatalogService.get_products(category=category, brand=brand, sort=sort)
    return products


@router.get("/search")
async def search_catalog(q: str, limit: int = 10):
    embedding = AIService.generate_embedding(q)
    results = CatalogService.search_products(q, embedding, limit)
    return {"results": results}
