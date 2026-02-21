# app/api/routers/cart.py

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, get_channel
from app.schemas.schemas import CartItemAdd
from app.services.cart_service import (
    add_item_to_cart,
    remove_item_from_cart,
    get_active_cart,
    get_hydrated_cart,
    update_cart_item_quantity
)
from app.enums.db_enums import ChannelEnum
from pydantic import BaseModel

router = APIRouter(prefix="/cart", tags=["Cart"])


# @router.get("")
# def my_cart(
#     db: Session = Depends(get_db),
#     user=Depends(get_current_user),
# ):
#     return get_active_cart(db, user_id=user.id)

@router.get("")
def my_cart(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Now this returns a fully detailed JSON response for the frontend!
    return get_hydrated_cart(db, user_id=user.id)

@router.post("/items")
def add_cart_item(
    payload: CartItemAdd,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    channel: ChannelEnum = Depends(get_channel),
):
    try:
        cart = add_item_to_cart(
            db=db,
            user_id=user.id,
            session_id=session_id,
            product_variant_id=payload.product_variant_id,
            quantity=payload.quantity,
            channel=channel,
            impression_id=getattr(payload, "impression_id", None),
        )
        db.commit()
        return cart
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/items/{variant_id}")
def remove_cart_item(
    variant_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    channel: ChannelEnum = Depends(get_channel),
):
    removed = remove_item_from_cart(
        db=db,
        user_id=user.id,
        session_id=session_id,
        product_variant_id=variant_id,
        channel=channel,
    )
    db.commit()

    if not removed:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"status": "removed"}

class CartItemUpdate(BaseModel):
    quantity: int

@router.put("/items/{variant_id}")
def update_cart_item(
    variant_id: uuid.UUID,
    payload: CartItemUpdate,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    channel: ChannelEnum = Depends(get_channel),
):
    try:
        cart = update_cart_item_quantity(
            db=db,
            user_id=user.id,
            session_id=session_id,
            product_variant_id=variant_id,
            new_quantity=payload.quantity,
            channel=channel,
            source="user_action"
        )
        return {"status": "success", "message": "Quantity updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")