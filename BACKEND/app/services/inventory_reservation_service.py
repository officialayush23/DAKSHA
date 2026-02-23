# app/services/inventory_reservation_service.py
# app/services/inventory_reservation_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID

def reserve_inventory_delivery(db: Session, checkout_id: UUID, cart_id: UUID):
    """Reserves warehouse stock for delivery."""
    db.execute(text("""
        INSERT INTO inventory_reservations
        (checkout_id, product_variant_id, quantity, source)
        SELECT :checkout_id, ci.product_variant_id, ci.quantity, 'warehouse'
        FROM cart_items ci
        WHERE ci.cart_id = :cart_id
    """), {"checkout_id": checkout_id, "cart_id": cart_id})

    db.execute(text("""
        UPDATE global_inventory gi
        SET reserved_stock = reserved_stock - ci.quantity,
            total_stock   = total_stock - ci.quantity
        FROM cart_items ci
        WHERE ci.cart_id = :cart_id
          AND gi.product_variant_id = ci.product_variant_id
          AND gi.reserved_stock >= ci.quantity
    """), {"cart_id": cart_id})

def reserve_inventory_pickup(db: Session, checkout_id: UUID, cart_id: UUID, store_id: UUID):
    """Reserves store stock for pickup."""
    db.execute(text("""
        INSERT INTO inventory_reservations
        (checkout_id, product_variant_id, store_id, quantity, source)
        SELECT :checkout_id, ci.product_variant_id, :store_id, ci.quantity, 'store'
        FROM cart_items ci
        WHERE ci.cart_id = :cart_id
    """), {"checkout_id": checkout_id, "cart_id": cart_id, "store_id": store_id})

    db.execute(text("""
        UPDATE store_inventory si
        SET in_stock = in_stock - ci.quantity,
            reserved_for_pickup = COALESCE(reserved_for_pickup, 0) + ci.quantity
        FROM cart_items ci
        WHERE ci.cart_id = :cart_id
          AND si.store_id = :store_id
          AND si.product_variant_id = ci.product_variant_id
    """), {"cart_id": cart_id, "store_id": store_id})

    db.execute(text("""
        UPDATE global_inventory gi
        SET assigned_stock = assigned_stock - ci.quantity
        FROM cart_items ci
        WHERE ci.cart_id = :cart_id
          AND gi.product_variant_id = ci.product_variant_id
    """), {"cart_id": cart_id})

def release_reservations(db: Session, checkout_id: UUID):
    """Restores stock for failed/expired reservations."""
    rows = db.execute(text("""
        SELECT * FROM inventory_reservations WHERE checkout_id = :cid
    """), {"cid": checkout_id}).fetchall()

    for r in rows:
        if r.source == "warehouse":
            db.execute(text("""
                UPDATE global_inventory
                SET reserved_stock = reserved_stock + :qty,
                    total_stock   = total_stock + :qty
                WHERE product_variant_id = :vid
            """), {"qty": r.quantity, "vid": r.product_variant_id})
        else:
            db.execute(text("""
                UPDATE store_inventory
                SET in_stock = in_stock + :qty,
                    reserved_for_pickup = reserved_for_pickup - :qty
                WHERE store_id = :sid AND product_variant_id = :vid
            """), {"qty": r.quantity, "vid": r.product_variant_id, "sid": r.store_id})

            db.execute(text("""
                UPDATE global_inventory
                SET assigned_stock = assigned_stock + :qty
                WHERE product_variant_id = :vid
            """), {"qty": r.quantity, "vid": r.product_variant_id})

    db.execute(text("DELETE FROM inventory_reservations WHERE checkout_id = :cid"), {"cid": checkout_id})

def finalize_reservations(db: Session, checkout_id: UUID):
    """
    Called strictly AFTER successful payment.
    Cleans up temporary holds. Physical stock was already deducted during reservation.
    """
    rows = db.execute(text("""
        SELECT * FROM inventory_reservations WHERE checkout_id = :cid
    """), {"cid": checkout_id}).fetchall()

    for r in rows:
        if r.source == "store":
            # Stock formally leaves the store ecosystem
            db.execute(text("""
                UPDATE store_inventory
                SET reserved_for_pickup = reserved_for_pickup - :qty
                WHERE store_id = :sid AND product_variant_id = :vid
            """), {"qty": r.quantity, "vid": r.product_variant_id, "sid": r.store_id})

    # Erase ledger
    db.execute(text("DELETE FROM inventory_reservations WHERE checkout_id = :cid"), {"cid": checkout_id})
    
def release_inventory(db: Session, cart_id: UUID):
    row = db.execute(text("SELECT id FROM checkout_sessions WHERE cart_id = :cid AND inventory_locked = TRUE LIMIT 1"), {"cid": cart_id}).fetchone()
    if row:
        release_reservations(db, row.id)