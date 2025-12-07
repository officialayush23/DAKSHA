from fastapi import APIRouter
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/search")
async def search_catalog(q: str, limit: int = 10):
    embedding = AIService.generate_embedding(q)
    results = CatalogService.search_products(q, embedding, limit)
    return {"results": results}
