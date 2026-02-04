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

def clear_cart(db: Session, cart: Cart):
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
