# app/routers/cart.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.schemas.schemas import AddToCartRequest, CheckoutRequest, CartItemUpdate
from app.services.commerce_service import CommerceService

router = APIRouter(prefix="/cart", tags=["Cart"])




@router.get("")
async def get_cart(user_id: str = Depends(get_current_user_id)):
    """Get current user's cart"""
    return CommerceService.get_cart_snapshot(user_id) or {
        "cart": None,
        "items": [],
        "pricing": None,
        "fulfillment_preview": None,
    }


@router.post("")
async def add_to_cart(
    data: AddToCartRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Add item to cart"""
    return CommerceService.add_item(
        user_id=user_id,
        variant_id=data.variant_id,
        qty=data.quantity,
        fulfillment_location_id=data.fulfillment_location_id,
    )


@router.post("/checkout")
async def checkout(
    data: CheckoutRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Checkout cart - create order"""
    return CommerceService.checkout_commit(
        user_id=user_id,
        order_type=data.order_type,
        pickup_location_id=data.pickup_fulfillment_location_id,
        address_id=data.address_id,
        promotion_code=data.promotion_code,
    )


@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Remove item from cart"""
    from app.core.database import supabase
    from fastapi import HTTPException
    
    try:
        # Verify item belongs to user's cart
        cart = CommerceService.get_cart_snapshot(user_id)
        if not cart or not cart.get("cart"):
            raise HTTPException(404, "Cart not found")
        
        item = (
            supabase.table("cart_items")
            .select("id, cart_id")
            .eq("id", item_id)
            .eq("cart_id", cart["cart"]["id"])
            .maybe_single()
            .execute()
        ).data
        
        if not item:
            raise HTTPException(404, "Item not found in cart")
        
        supabase.table("cart_items").delete().eq("id", item_id).execute()
        
        return {"status": "removed", "item_id": item_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to remove item: {str(e)}")


@router.patch("/items/{item_id}")
async def update_cart_item_quantity(
    item_id: str,
    data: CartItemUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Update cart item quantity"""
    return CommerceService.update_item_quantity(
        user_id=user_id,
        item_id=item_id,
        quantity=data.quantity
    )


@router.get("/checkout/preview")
async def checkout_preview(
    order_type: str,
    pickup_location_id: str = None,
    address_id: str = None,
    promotion_code: str = None,
    user_id: str = Depends(get_current_user_id)
):
    """Preview checkout without committing"""
    return CommerceService.checkout_preview(
        user_id=user_id,
        order_type=order_type,
        pickup_location_id=pickup_location_id,
        address_id=address_id,
        promotion_code=promotion_code,
    )

