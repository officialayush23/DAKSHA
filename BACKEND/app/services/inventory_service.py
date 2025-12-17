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
        return (
            supabase.table("inventory")
            .select(
                "*, product_variants(*, products(name, base_price, is_active))"
            )
            .eq("fulfillment_location_id", store_id)
            .order("product_variant_id")
            .execute()
        ).data or []

    # ---------------------------------------------------------
    # FULL UPDATE (STORE / WAREHOUSE)
    # ---------------------------------------------------------
    @staticmethod
    async def full_update(data):
        """
        Store / Warehouse can update:
        - quantity_on_hand
        - physical layout (aisle, bay, shelf, section)
        Product metadata is NOT editable here.
        """

        # 1️⃣ Validate product variant + product state
        pv = (
            supabase.table("product_variants")
            .select("id, products(is_active)")
            .eq("id", data.variant_id)
            .single()
            .execute()
        ).data

        if not pv:
            raise HTTPException(404, "Product variant does not exist")

        if not pv["products"]["is_active"]:
            raise HTTPException(400, "Inactive product cannot be stocked")

        # 2️⃣ Validate inventory row
        row = (
            supabase.table("inventory")
            .select("*")
            .eq("product_variant_id", data.variant_id)
            .eq("fulfillment_location_id", data.store_id)
            .maybe_single()
            .execute()
        ).data

        if not row:
            raise HTTPException(404, "Inventory row not found")

        # 3️⃣ Build allowed updates
        updates = {}
        for field in [
            "quantity_on_hand",
            "section_id",
            "aisle_number",
            "bay_number",
            "shelf_height",
            "display_location",
        ]:
            value = getattr(data, field, None)
            if value is not None:
                updates[field] = value

        if not updates:
            return row

        # 4️⃣ HARD GUARANTEE: quantity >= 0
        if "quantity_on_hand" in updates and updates["quantity_on_hand"] < 0:
            updates["quantity_on_hand"] = 0

        # 5️⃣ Persist
        updated = (
            supabase.table("inventory")
            .update(updates)
            .eq("id", row["id"])
            .execute()
        ).data[0]

        # 6️⃣ Auto alerts (low / out of stock)
        await InventoryAlertService.evaluate_and_trigger(updated)

        # 7️⃣ Realtime push
        await EventBus.notify_inventory_update(
            data.store_id,
            {
                "inventory_id": updated["id"],
                "product_variant_id": updated["product_variant_id"],
                "quantity_on_hand": updated["quantity_on_hand"],
                "quantity_reserved": updated.get("quantity_reserved", 0),
            },
        )

        return updated
    

    @staticmethod
    def trending_near_city(city: str, limit: int = 8):
        """
        Combines:
        - local inventory availability
        - recent order velocity
        """

        res = (
            supabase.rpc(
                "get_trending_products_near_city",
                {
                    "p_city": city,
                    "p_limit": limit,
                }
            )
            .execute()
        )

        items = res.data or []

        return [
            {
                "id": p["product_id"],
                "name": p["name"],
                "base_price": p["base_price"],
                "image_url": p.get("image_url"),
                "badge": "Low stock" if p["available_qty"] < 5 else None,
                "agent_reason": f"Popular in {city}",
                "inventory": {
                    "available": p["available_qty"] > 0,
                    "quantity": p["available_qty"],
                },
            }
            for p in items
        ]


    # ---------------------------------------------------------
    # GENERIC DASHBOARD (STORE / WAREHOUSE)
    # ---------------------------------------------------------
    @staticmethod
    def get_fulfillment_dashboard(fulfillment_location_id: str):
        return (
            supabase.table("inventory")
            .select(
                "*, product_variants(*, products(name, base_price))"
            )
            .eq("fulfillment_location_id", fulfillment_location_id)
            .order("product_variant_id")
            .execute()
        ).data or []
