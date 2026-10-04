# app/services/cart_service.py
"""
Cart service.

One cart per user, shared by every channel (web/PWA, kiosk, Telegram, chat
agent). Earlier versions keyed carts by (user, session), so logging in at a
kiosk started an empty cart; the unified cart fixes that.

Availability comes from app/services/stock.py, the same helper the catalog
and the agents use.
"""
import uuid
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.background import dispatch
from app.enums.db_enums import ChannelEnum, EntityTypeEnum, EventTypeEnum
from app.models.models import Cart, CartItem, GlobalInventory, UserSession
from app.services.event_service import emit_event
from app.services.stock import sellable

_SOURCES = {"user_action", "agent_action", "system"}


def _source(s: str) -> str:
    return s if s in _SOURCES else "user_action"


def available_stock(inv: Optional[GlobalInventory]) -> int:
    # warehouse pool + store shelves; the checkout hold enforces the exact source
    return sellable(inv)


def _owned_session(db: Session, user_id, session_id):
    """Events reference sessions.id; ignore ids that aren't this user's session."""
    if not session_id:
        return None
    try:
        s = db.get(UserSession, uuid.UUID(str(session_id)))
    except (ValueError, TypeError):
        return None
    return s.id if s and s.user_id == user_id else None


def _refresh_prefs(user_id):
    from app.worker.tasks import refresh_user_preferences
    dispatch(refresh_user_preferences, str(user_id))


# ======================================================
# CART CORE
# ======================================================

def get_active_cart(db: Session, *, user_id: uuid.UUID) -> Optional[Cart]:
    return (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .order_by(Cart.updated_at.desc())
        .first()
    )


def get_or_create_cart(db: Session, *, user_id: uuid.UUID, session_id: Optional[uuid.UUID] = None) -> Cart:
    cart = get_active_cart(db, user_id=user_id)
    if cart:
        return cart
    cart = Cart(user_id=user_id, session_id=_owned_session(db, user_id, session_id))
    db.add(cart)
    db.flush()
    return cart


def get_hydrated_cart(db: Session, user_id: uuid.UUID) -> dict:
    from app.services.pricing_service import resolve_variant_price

    cart = get_active_cart(db, user_id=user_id)
    if not cart:
        return {"cart_id": None, "total_items": 0, "grand_total": 0.0, "items": []}

    items, total_items, grand_total = [], 0, 0.0
    for item in cart.items:
        variant = item.variant
        product = variant.product
        try:
            price = resolve_variant_price(db, variant)
        except Exception:
            price = {"base_price": float(variant.base_price or 0), "final_price": float(variant.base_price or 0)}
        line = round(price["final_price"] * item.quantity, 2)
        total_items += item.quantity
        grand_total += line
        items.append({
            "variant_id": str(variant.id),
            "product_id": str(product.id),
            "name": product.name,
            "brand": product.brand,
            "quantity": item.quantity,
            "color": variant.color,
            "size": variant.size,
            "image": variant.images[0].image_url if getattr(variant, "images", None) else None,
            "unit_price": price["final_price"],
            "base_price": price["base_price"],
            "line_total": line,
            "in_stock": available_stock(db.get(GlobalInventory, variant.id)),
        })
    return {
        "cart_id": str(cart.id),
        "updated_at": cart.updated_at,
        "total_items": total_items,
        "grand_total": round(grand_total, 2),
        "items": items,
    }


# ======================================================
# CART MUTATIONS
# ======================================================

def add_item_to_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: Optional[uuid.UUID],
    product_variant_id: uuid.UUID,
    quantity: int,
    channel: ChannelEnum,
    impression_id: Optional[uuid.UUID] = None,
    source: str = "user_action",
) -> Cart:
    try:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > 20:
            raise ValueError("At most 20 units of one item per order")

        inventory = db.get(GlobalInventory, product_variant_id)
        if not inventory:
            raise ValueError("This item is not stocked")
        available = available_stock(inventory)

        cart = get_or_create_cart(db, user_id=user_id, session_id=session_id)
        item = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.product_variant_id == product_variant_id)
            .first()
        )
        wanted = (item.quantity if item else 0) + quantity
        if wanted > available:
            raise ValueError(f"Only {available} units available")
        if item:
            item.quantity = wanted
        else:
            db.add(CartItem(cart_id=cart.id, product_variant_id=product_variant_id, quantity=quantity))
        cart.updated_at = func.now()

        emit_event(
            db=db, event_type=EventTypeEnum.add_to_cart, channel=channel, user_id=user_id,
            session_id=_owned_session(db, user_id, session_id),
            entity_type=EntityTypeEnum.cart, entity_id=cart.id, quantity=quantity,
            metadata={"variant_id": str(product_variant_id),
                      "impression_id": str(impression_id) if impression_id else None},
            source=_source(source),
        )
        db.commit()
        db.refresh(cart)
        _refresh_prefs(user_id)
        return cart
    except Exception:
        db.rollback()
        raise


def remove_item_from_cart(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: Optional[uuid.UUID],
    product_variant_id: uuid.UUID,
    channel: ChannelEnum,
    source: str = "user_action",
) -> bool:
    try:
        cart = get_active_cart(db, user_id=user_id)
        if not cart:
            return False
        item = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.product_variant_id == product_variant_id)
            .first()
        )
        if not item:
            return False
        qty = item.quantity
        db.delete(item)
        cart.updated_at = func.now()
        emit_event(
            db=db, event_type=EventTypeEnum.remove_from_cart, channel=channel, user_id=user_id,
            session_id=_owned_session(db, user_id, session_id),
            entity_type=EntityTypeEnum.cart, entity_id=cart.id, quantity=qty,
            metadata={"variant_id": str(product_variant_id)}, source=_source(source),
        )
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def update_cart_item_quantity(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: Optional[uuid.UUID],
    product_variant_id: uuid.UUID,
    new_quantity: int,
    channel: ChannelEnum,
    source: str = "user_action",
) -> Optional[Cart]:
    try:
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if new_quantity == 0:
            remove_item_from_cart(db=db, user_id=user_id, session_id=session_id,
                                  product_variant_id=product_variant_id, channel=channel, source=source)
            return get_active_cart(db, user_id=user_id)
        if new_quantity > 20:
            raise ValueError("At most 20 units of one item per order")

        cart = get_active_cart(db, user_id=user_id)
        if not cart:
            raise ValueError("Cart not found")
        item = (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart.id, CartItem.product_variant_id == product_variant_id)
            .first()
        )
        if not item:
            raise ValueError("Item not found in cart")
        available = available_stock(db.get(GlobalInventory, product_variant_id))
        if new_quantity > available:
            raise ValueError(f"Only {available} units available in stock")

        delta = new_quantity - item.quantity
        if delta == 0:
            return cart
        item.quantity = new_quantity
        cart.updated_at = func.now()
        emit_event(
            db=db, event_type=EventTypeEnum.add_to_cart if delta > 0 else EventTypeEnum.remove_from_cart,
            channel=channel, user_id=user_id, session_id=_owned_session(db, user_id, session_id),
            entity_type=EntityTypeEnum.cart, entity_id=cart.id, quantity=abs(delta),
            metadata={"variant_id": str(product_variant_id)}, source=_source(source),
        )
        db.commit()
        db.refresh(cart)
        return cart
    except Exception:
        db.rollback()
        raise
