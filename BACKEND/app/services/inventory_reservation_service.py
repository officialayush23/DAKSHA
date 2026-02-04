# app/services/inventory_reservation_service.py
from sqlalchemy.orm import Session
from app.models.models import CartItem, GlobalInventory

def reserve_inventory(db: Session, cart_id):
    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()

    for item in items:
        inv = db.query(GlobalInventory).get(item.product_variant_id)

        if not inv or inv.reserved_stock < item.quantity:
            raise ValueError("Insufficient stock")

        inv.reserved_stock -= item.quantity
        inv.assigned_stock += item.quantity

    db.commit()


def release_inventory(db: Session, cart_id):
    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()

    for item in items:
        inv = db.query(GlobalInventory).get(item.product_variant_id)
        inv.reserved_stock += item.quantity
        inv.assigned_stock -= item.quantity

    db.commit()
