# app/services/inventory_alert_service.py
from app.core.database import supabase
from app.core.redis_bus import EventBus

class InventoryAlertService:

    @staticmethod
    async def evaluate_and_trigger(inventory_row: dict):
        """
        Called after ANY inventory quantity change.
        """

        qty = inventory_row["quantity_on_hand"]
        threshold = inventory_row.get("low_stock_threshold", 5)

        alert_type = None
        if qty <= 0:
            alert_type = "out_of_stock"
        elif qty <= threshold:
            alert_type = "low_stock"

        if not alert_type:
            return

        # Prevent duplicate active alerts
        existing = (
            supabase.table("inventory_alerts")
            .select("id")
            .eq("fulfillment_location_id", inventory_row["fulfillment_location_id"])
            .eq("product_variant_id", inventory_row["product_variant_id"])
            .eq("alert_type", alert_type)
            .eq("acknowledged", False)
            .maybe_single()
            .execute()
        )

        if existing.data:
            return

        alert = (
            supabase.table("inventory_alerts")
            .insert({
                "fulfillment_location_id": inventory_row["fulfillment_location_id"],
                "product_variant_id": inventory_row["product_variant_id"],
                "alert_type": alert_type,
                "threshold": threshold,
                "current_quantity": qty,
            })
            .execute()
        ).data[0]

        # Realtime broadcast
        await EventBus.notify_inventory_alert(
            inventory_row["fulfillment_location_id"],
            alert
        )
