# app/routers/products.py
from fastapi import APIRouter, HTTPException
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/{product_id}")
async def get_product(product_id: str):
    return await ProductService.get_pdp(product_id)
