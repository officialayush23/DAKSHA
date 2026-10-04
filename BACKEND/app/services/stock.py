# app/services/stock.py
"""
One definition of "in stock" for the whole codebase.

The admin tools maintain this invariant on global_inventory:

    total_stock = reserved_stock + assigned_stock

where, despite its name, `reserved_stock` is the FREE warehouse pool (units
not yet allocated to a store) and `assigned_stock` is what has been moved to
stores. Several call sites used `total - reserved - assigned`, which is zero
whenever the invariant holds, so search results and image search silently
dropped almost every product. Use these helpers instead.
"""
from typing import Optional


def warehouse_available(inv) -> int:
    """Units that can ship from the warehouse (delivery orders)."""
    return max(int(getattr(inv, "reserved_stock", 0) or 0), 0) if inv else 0


def sellable(inv) -> int:
    """Units sellable anywhere: warehouse pool + units sitting in stores."""
    if not inv:
        return 0
    return max(int(inv.reserved_stock or 0), 0) + max(int(inv.assigned_stock or 0), 0)


def store_available(store_inv) -> int:
    """Units a store can still hand over (holds are already subtracted from in_stock)."""
    return max(int(getattr(store_inv, "in_stock", 0) or 0), 0) if store_inv else 0
