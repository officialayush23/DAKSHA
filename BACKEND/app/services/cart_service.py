# app/services/cart_service.py

import uuid
from typing import Optional
from app.worker.tasks import refresh_user_preferences
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
    db.flush()  # IMPORTANT: no commit here, handled by parent functions
    return cart

def get_hydrated_cart(db: Session, user_id: uuid.UUID) -> dict:
    cart = get_active_cart(db, user_id=user_id)
    
    if not cart:
        return {
            "cart_id": None, 
            "total_items": 0, 
            "grand_total": 0.0, 
            "items": []
        }

    items_data = []
    total_items = 0

    for item in cart.items:
        variant = item.variant
        product = variant.product
        total_items += item.quantity

        # We only return IDs and basic metadata. 
        # Frontend will fetch the "Live Price" using product_id.
        items_data.append({
            "variant_id": str(variant.id),
            "product_id": str(product.id),
            "quantity": item.quantity,
            "color": variant.color,
            "size": variant.size,
        })

    return {
        "cart_id": str(cart.id),
        "updated_at": cart.updated_at,
        "total_items": total_items,
        "items": items_data
        # grand_total is removed here because backend doesn't know the real price
    }

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
    source: str = "user_action",  # <-- ADDED SOURCE TRACKING
) -> Cart:
    try:
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
            source=source,  # <-- PASSING SOURCE TO EVENT
        )
        
        refresh_user_preferences.delay(str(user_id))

        db.commit()  # <-- COMMIT MOVED HERE
        db.refresh(cart)
        return cart

    except Exception as e:
        db.rollback()  # <-- ROLLBACK ON ERROR
        raise e


def remove_item_from_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    product_variant_id: uuid.UUID,
    channel: ChannelEnum,
    source: str = "user_action",  # <-- ADDED SOURCE TRACKING
) -> bool:
    try:
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
            source=source,  # <-- PASSING SOURCE TO EVENT
        )

        db.commit()  # <-- COMMIT MOVED HERE
        return True

    except Exception as e:
        db.rollback()  # <-- ROLLBACK ON ERROR
        raise e
    

# Add this inside app/services/cart_service.py

def update_cart_item_quantity(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    product_variant_id: uuid.UUID,
    new_quantity: int,
    channel: ChannelEnum,
    source: str = "user_action",
) -> Cart:
    try:
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")

        # If they set quantity to 0, just reuse the remove function
        if new_quantity == 0:
            remove_item_from_cart(
                db=db, 
                user_id=user_id, 
                session_id=session_id, 
                product_variant_id=product_variant_id, 
                channel=channel, 
                source=source
            )
            return get_active_cart(db, user_id=user_id)

        cart = (
            db.query(Cart)
            .filter(Cart.user_id == user_id, Cart.session_id == session_id)
            .first()
        )
        if not cart:
            raise ValueError("Cart not found")

        item = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.product_variant_id == product_variant_id)
            .first()
        )
        if not item:
            raise ValueError("Item not found in cart")

        # --- HARD RULE: Inventory availability ---
        inventory = db.get(GlobalInventory, product_variant_id)
        if not inventory:
            raise ValueError("Inventory not found")

        available = inventory.total_stock - inventory.reserved_stock
        if available < new_quantity:
            raise ValueError(f"Only {available} units available in stock")

        # Calculate the difference (delta) to log the correct event
        delta = new_quantity - item.quantity
        if delta == 0:
            return cart  # No change was actually made

        # Update the state
        item.quantity = new_quantity
        cart.updated_at = func.now()

        # Decide whether to log this as adding more or removing some
        event_type = EventTypeEnum.add_to_cart if delta > 0 else EventTypeEnum.remove_from_cart
        
        # --- EVENT ---
        emit_event(
            db=db,
            event_type=event_type,
            channel=channel,
            user_id=user_id,
            session_id=session_id,
            entity_type=EntityTypeEnum.cart,
            entity_id=cart.id,
            quantity=abs(delta),  # Event quantity should always be positive
            metadata={"variant_id": str(product_variant_id)},
            source=source,
        )

        db.commit()
        db.refresh(cart)
        return cart

    except Exception as e:
        db.rollback()
        raise e