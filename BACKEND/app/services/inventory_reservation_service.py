# app/services/inventory_reservation_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID

def reserve_inventory(db: Session, cart_id: UUID) -> bool:
    """
    Locks inventory for a cart. 
    Logic: Available = Total - Reserved. 
    Action: Reserved += Quantity.
    """
    try:
        # We assume checking against Global Inventory for online flow
        sql = text("""
            UPDATE global_inventory gi
            SET reserved_stock = reserved_stock + ci.quantity
            FROM cart_items ci
            WHERE ci.cart_id = :cid
              AND gi.product_variant_id = ci.product_variant_id
              AND (gi.total_stock - gi.reserved_stock) >= ci.quantity
        """)
        result = db.execute(sql, {"cid": cart_id})
        return result.rowcount > 0
    except Exception:
        return False

def release_inventory(db: Session, cart_id: UUID):
    """
    Reverses reservation on timeout or cancellation.
    Action: Reserved -= Quantity.
    """
    sql = text("""
        UPDATE global_inventory gi
        SET reserved_stock = reserved_stock - ci.quantity
        FROM cart_items ci
        WHERE ci.cart_id = :cid
          AND gi.product_variant_id = ci.product_variant_id
    """)
    db.execute(sql, {"cid": cart_id})
    db.commit()