from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.commerce import AddToCartRequest
from app.services.commerce_service import CommerceService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.post("/add")
async def add_to_cart(
    payload: AddToCartRequest, user_id: str = Depends(get_current_user_id)
):
    return await CommerceService.add_to_cart(
        user_id, payload.variant_id, payload.store_id, payload.quantity
    )
