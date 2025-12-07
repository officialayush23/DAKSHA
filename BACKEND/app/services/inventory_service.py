from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus
from app.models.management import InventoryFullUpdate


class InventoryService:
    @staticmethod
    def get_store_dashboard(store_id: str):
        """
        Initial load for the Store Manager's Tablet.
        Returns all inventory for this specific store with variant + product info.
        """
        res = (
            supabase.table("inventory")
            .select(
                "*, "
                "product_variants("
                "   sku, color_name, size_label, "
                "   products(name)"
                ")"
            )
            .eq("store_id", store_id)
            .execute()
        )
        return res.data

    @staticmethod
    async def full_update(data: InventoryFullUpdate) -> dict:
        """
        'God Mode' inventory update:
        - Optimistic locking via version
        - Updates quantity + location fields
        - Broadcasts realtime update to store dashboard / kiosks
        """
        # 1. Get Current Version
        current = (
            supabase.table("inventory")
            .select("id, version")
            .eq("store_id", data.store_id)
            .eq("product_variant_id", data.variant_id)
            .single()
            .execute()
        )

        if not current.data:
            raise HTTPException(status_code=404, detail="Item not found in this store")

        current_version = current.data["version"]

        # 2. Prepare Update Payload (strip Nones + IDs)
        payload = {k: v for k, v in data.dict().items() if v is not None}

        # These are identifiers, not columns to update
        payload.pop("variant_id", None)
        payload.pop("store_id", None)

        # Bump version
        payload["version"] = current_version + 1

        # 3. Execute Update with Optimistic Lock
        res = (
            supabase.table("inventory")
            .update(payload)
            .eq("store_id", data.store_id)
            .eq("product_variant_id", data.variant_id)
            .eq("version", current_version)
            .execute()
        )

        if not res.data:
            # Someone else changed it between read & write
            raise HTTPException(
                status_code=409,
                detail="Inventory modified by someone else. Retry.",
            )

        updated_item = res.data[0]

        # 4. Realtime broadcast via EventBus
        await EventBus.notify_store_inventory(
            data.store_id,
            {
                "inventory_id": updated_item["id"],
                "product_variant_id": updated_item["product_variant_id"],
                "quantity_on_hand": updated_item["quantity_on_hand"],
                "quantity_reserved": updated_item.get("quantity_reserved", 0),
                "aisle_number": updated_item.get("aisle_number"),
                "bay_number": updated_item.get("bay_number"),
                "shelf_height": updated_item.get("shelf_height"),
                "display_location": updated_item.get("display_location"),
            },
        )

        return updated_item
