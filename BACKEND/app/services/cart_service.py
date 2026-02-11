# app/services/cart_service.py

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    Cart,
    CartItem,
    GlobalInventory,
)
from app.services.event_service import emit_event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum, ChannelEnum


# ======================================================
# CART CORE
# ======================================================

def get_or_create_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> Cart:
    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.session_id == session_id,
        )
        .first()
    )

    if cart:
        return cart

    cart = Cart(
        user_id=user_id,
        session_id=session_id,
    )
    db.add(cart)
    db.flush()  # IMPORTANT: no commit here
    return cart


def get_active_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> Optional[Cart]:
    return (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .order_by(Cart.updated_at.desc())
        .first()
    )


# ======================================================
# CART MUTATIONS
# ======================================================

def add_item_to_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    product_variant_id: uuid.UUID,
    quantity: int,
    channel: ChannelEnum,
    impression_id: Optional[uuid.UUID] = None,
) -> Cart:
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    # --- HARD RULE: inventory availability ---
    inventory = db.get(GlobalInventory, product_variant_id)
    if not inventory:
        raise ValueError("Inventory not found")

    available = inventory.total_stock - inventory.reserved_stock
    if available < quantity:
        raise ValueError(f"Only {available} units available")

    cart = get_or_create_cart(
        db,
        user_id=user_id,
        session_id=session_id,
    )

    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_variant_id == product_variant_id,
        )
        .first()
    )

    if item:
        if item.quantity + quantity > available:
            raise ValueError("Quantity exceeds available stock")
        item.quantity += quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_variant_id=product_variant_id,
            quantity=quantity,
        )
        db.add(item)

    cart.updated_at = func.now()

    # --- EVENT ---
    emit_event(
        db=db,
        event_type=EventTypeEnum.add_to_cart,
        channel=channel,
        user_id=user_id,
        session_id=session_id,
        entity_type=EntityTypeEnum.cart,
        entity_id=cart.id,
        quantity=quantity,
        metadata={
            "variant_id": str(product_variant_id),
            "impression_id": str(impression_id) if impression_id else None,
        },
    )

    return cart


def remove_item_from_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    product_variant_id: uuid.UUID,
    channel: ChannelEnum,
) -> bool:
    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user_id,
            Cart.session_id == session_id,
        )
        .first()
    )
    if not cart:
        return False

    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_variant_id == product_variant_id,
        )
        .first()
    )
    if not item:
        return False

    qty = item.quantity
    db.delete(item)
    cart.updated_at = func.now()

    emit_event(
        db=db,
        event_type=EventTypeEnum.remove_from_cart,
        channel=channel,
        user_id=user_id,
        session_id=session_id,
        entity_type=EntityTypeEnum.cart,
        entity_id=cart.id,
        quantity=qty,
        metadata={"variant_id": str(product_variant_id)},
    )

    return True
