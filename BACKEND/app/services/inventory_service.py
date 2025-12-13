# app/services/inventory_service.py

from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus
from app.services.inventory_alert_service import InventoryAlertService


class InventoryService:

    # ---------------------------------------------------------
    # STORE DASHBOARD LOAD
    # ---------------------------------------------------------
    @staticmethod
    def get_store_dashboard(store_id: str):
        """
        Load everything a store dashboard needs:
        - inventory
        - product + variant metadata
        """

        inv = (
            supabase.table("inventory")
            .select(
                "*, product_variants(*, products(name, base_price))"
            )
            .eq("fulfillment_location_id", store_id)
            .order("product_variant_id")
            .execute()
        )

        return inv.data or []

    # ---------------------------------------------------------
    # FULL UPDATE (manager correction)
    # ---------------------------------------------------------
    @staticmethod
    async def full_update(data):
        """
        Updates:
        - quantity_on_hand
        - aisle/bay/shelf
        - display location
        - section mapping
        AND triggers real-time dashboard updates.
        """

        # Validate row exists
        row = (
            supabase.table("inventory")
            .select("*")
            .eq("product_variant_id", data.variant_id)
            .eq("fulfillment_location_id", data.store_id)
            .maybe_single()
            .execute()
        ).data

        if not row:
            raise HTTPException(404, "Inventory row not found for this store")

        updates = {}
        for fld in [
            "quantity_on_hand",
            "section_id",
            "aisle_number",
            "bay_number",
            "shelf_height",
            "display_location",
        ]:
            val = getattr(data, fld)
            if val is not None:
                updates[fld] = val

        if not updates:
            return row

        updated = (
            supabase.table("inventory")
            .update(updates)
            .eq("product_variant_id", data.variant_id)
            .eq("fulfillment_location_id", data.store_id)
            .execute()
        ).data[0]

        await InventoryAlertService.evaluate_and_trigger(updated)

        # Realtime broadcast
        await EventBus.notify_store_inventory(
            data.store_id,
            {
                "inventory_id": updated["id"],
                "product_variant_id": updated["product_variant_id"],
                "quantity_on_hand": updated["quantity_on_hand"],
                "quantity_reserved": updated.get("quantity_reserved", 0),
            },
        )

        return updated
    
        

class InventoryService:
    ...

    # ---------------------------------------------------------
    # GENERIC FULFILLMENT DASHBOARD (STORE / WAREHOUSE)
    # ---------------------------------------------------------
    @staticmethod
    def get_fulfillment_dashboard(fulfillment_location_id: str):
        """
        Used by:
        - store dashboards
        - warehouse dashboards
        """

        res = (
            supabase.table("inventory")
            .select(
                "*, product_variants(*, products(name, base_price))"
            )
            .eq("fulfillment_location_id", fulfillment_location_id)
            .order("product_variant_id")
            .execute()
        )

        return res.data or []