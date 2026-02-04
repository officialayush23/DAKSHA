# app/services/cart_Service.py
from sqlalchemy.orm import Session
from app.models.models import Cart, CartItem
import uuid

def get_active_cart(db: Session, user_id: uuid.UUID):
    return (
        db.query(Cart)
        .filter(Cart.user_id == user_id)
        .order_by(Cart.updated_at.desc())
        .first()
    )

def get_cart_items(db: Session, cart: Cart):
    return (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

from app.services.event_service import emit_event
from app.enums.db_enums import EventTypeEnum, EntityTypeEnum



def remove_from_cart(db: Session, user, session_id, variant_id):
    cart = (
        db.query(Cart)
        .filter(
            Cart.user_id == user.id,
            Cart.session_id == session_id,
        )
        .first()
    )

    if not cart:
        return None

    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_variant_id == variant_id,
        )
        .first()
    )

    if not item:
        return None

    qty = item.quantity
    db.delete(item)
    db.commit()

    # 🔥 EVENT: remove_from_cart
    emit_event(
        db=db,
        user_id=user.id,
        session_id=session_id,
        channel=None,
        event_type=EventTypeEnum.remove_from_cart,
        entity_type=EntityTypeEnum.cart,
        entity_id=cart.id,
        quantity=qty,
    )

    return {"removed": True}