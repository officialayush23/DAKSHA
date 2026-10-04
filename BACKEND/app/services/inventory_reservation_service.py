# app/services/inventory_reservation_service.py
"""
Stock holds for checkout.

Ledger semantics (see app/services/stock.py):
  global_inventory   total_stock = reserved_stock (free warehouse pool) + assigned_stock (in stores)
  store_inventory    in_stock = units on the shelf that are not held; reserved_for_pickup = held units

A hold moves units out of the free pool immediately and records them in
inventory_reservations; release puts them back, finalize just clears the
ledger. Every move is ONE guarded UPDATE:

    UPDATE global_inventory SET reserved_stock = reserved_stock - q, total_stock = total_stock - q
    WHERE product_variant_id = ? AND reserved_stock >= q

Postgres row-locks the target row and re-evaluates the WHERE clause on the
newest version, so two checkouts racing for the last unit cannot both win:
the loser updates 0 rows and we raise InsufficientStock. The old code had the
same WHERE clause but never looked at the row count, so a failed hold was
silently ignored and the order went through anyway.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class InsufficientStock(ValueError):
    def __init__(self, variant_id, wanted, where="warehouse"):
        super().__init__(f"Not enough stock at the {where} for one of your items (needed {wanted}). "
                         "Please reduce the quantity or choose another option.")
        self.variant_id = variant_id


def _cart_lines(db: Session, cart_id: UUID):
    rows = db.execute(text("""
        SELECT product_variant_id, quantity FROM cart_items WHERE cart_id = :cid ORDER BY product_variant_id
    """), {"cid": str(cart_id)}).fetchall()
    if not rows:
        raise ValueError("Cart is empty")
    return rows


def reserve_inventory_delivery(db: Session, checkout_id: UUID, cart_id: UUID, expires_at: datetime):
    """Hold warehouse stock for every cart line, or raise InsufficientStock (caller rolls back)."""
    # lines are processed in variant-id order so concurrent multi-item checkouts can't deadlock
    for line in _cart_lines(db, cart_id):
        held = db.execute(text("""
            UPDATE global_inventory
               SET reserved_stock = reserved_stock - :q,
                   total_stock    = total_stock - :q
             WHERE product_variant_id = :v AND reserved_stock >= :q
        """), {"q": line.quantity, "v": line.product_variant_id}).rowcount
        if held != 1:
            raise InsufficientStock(line.product_variant_id, line.quantity)
        db.execute(text("""
            INSERT INTO inventory_reservations (checkout_id, product_variant_id, quantity, source_type, expires_at)
            VALUES (:c, :v, :q, 'warehouse', :e)
        """), {"c": str(checkout_id), "v": line.product_variant_id, "q": line.quantity, "e": expires_at})


def reserve_inventory_pickup(db: Session, checkout_id: UUID, cart_id: UUID, store_id: UUID, expires_at: datetime):
    """Hold store stock for every cart line, or raise InsufficientStock."""
    for line in _cart_lines(db, cart_id):
        held = db.execute(text("""
            UPDATE store_inventory
               SET in_stock = in_stock - :q,
                   reserved_for_pickup = COALESCE(reserved_for_pickup, 0) + :q
             WHERE store_id = :s AND product_variant_id = :v AND in_stock >= :q
        """), {"q": line.quantity, "v": line.product_variant_id, "s": str(store_id)}).rowcount
        if held != 1:
            raise InsufficientStock(line.product_variant_id, line.quantity, where="store")
        db.execute(text("""
            UPDATE global_inventory
               SET assigned_stock = GREATEST(assigned_stock - :q, 0),
                   total_stock    = GREATEST(total_stock - :q, 0)
             WHERE product_variant_id = :v
        """), {"q": line.quantity, "v": line.product_variant_id})
        db.execute(text("""
            INSERT INTO inventory_reservations (checkout_id, product_variant_id, store_id, quantity, source_type, expires_at)
            VALUES (:c, :v, :s, :q, 'store', :e)
        """), {"c": str(checkout_id), "v": line.product_variant_id, "s": str(store_id), "q": line.quantity, "e": expires_at})


def release_reservations(db: Session, checkout_id: UUID):
    """Put held units back (payment failed, checkout expired or fulfilment changed)."""
    rows = db.execute(text("SELECT * FROM inventory_reservations WHERE checkout_id = :cid"),
                      {"cid": str(checkout_id)}).fetchall()
    for r in rows:
        if r.source_type == "warehouse":
            db.execute(text("""
                UPDATE global_inventory
                   SET reserved_stock = reserved_stock + :q, total_stock = total_stock + :q
                 WHERE product_variant_id = :v
            """), {"q": r.quantity, "v": r.product_variant_id})
        else:
            db.execute(text("""
                UPDATE store_inventory
                   SET in_stock = in_stock + :q,
                       reserved_for_pickup = GREATEST(COALESCE(reserved_for_pickup, 0) - :q, 0)
                 WHERE store_id = :s AND product_variant_id = :v
            """), {"q": r.quantity, "v": r.product_variant_id, "s": r.store_id})
            db.execute(text("""
                UPDATE global_inventory
                   SET assigned_stock = assigned_stock + :q, total_stock = total_stock + :q
                 WHERE product_variant_id = :v
            """), {"q": r.quantity, "v": r.product_variant_id})
    db.execute(text("DELETE FROM inventory_reservations WHERE checkout_id = :cid"), {"cid": str(checkout_id)})


def finalize_reservations(db: Session, checkout_id: UUID):
    """After a successful payment: units already left the pools at hold time; clear the ledger."""
    rows = db.execute(text("SELECT * FROM inventory_reservations WHERE checkout_id = :cid"),
                      {"cid": str(checkout_id)}).fetchall()
    for r in rows:
        if r.source_type == "store":
            db.execute(text("""
                UPDATE store_inventory
                   SET reserved_for_pickup = GREATEST(COALESCE(reserved_for_pickup, 0) - :q, 0)
                 WHERE store_id = :s AND product_variant_id = :v
            """), {"q": r.quantity, "v": r.product_variant_id, "s": r.store_id})
    db.execute(text("DELETE FROM inventory_reservations WHERE checkout_id = :cid"), {"cid": str(checkout_id)})


def release_inventory(db: Session, cart_id: UUID):
    """Backward compatibility wrapper for tasks/cart clears."""
    row = db.execute(text("""
        SELECT id FROM checkout_sessions WHERE cart_id = :cid AND inventory_locked = TRUE LIMIT 1
    """), {"cid": str(cart_id)}).fetchone()
    if row:
        release_reservations(db, row.id)
