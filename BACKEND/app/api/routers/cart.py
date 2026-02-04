# app/api/routers/cart.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.services.cart_service import get_active_cart, get_cart_items
from uuid import UUID
from app.services.user_services import remove_from_cart

router = APIRouter(prefix="/user/cart", tags=["Cart"])

@router.get("")
def view_cart(db: Session = Depends(get_db), user=Depends(get_current_user)):
    cart = get_active_cart(db, user.id)
    if not cart:
        return {"cart": None}

    items = get_cart_items(db, cart)
    return {
        "cart_id": cart.id,
        "items": [
            {
                "variant_id": i.product_variant_id,
                "quantity": i.quantity,
                "price": i.variant.base_price,
                "sku": i.variant.sku,
            }
            for i in items
        ],
    }




