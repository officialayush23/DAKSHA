from fastapi import HTTPException
from app.database import supabase


class AllocationService:

    @staticmethod
    def allocate(order_type: str, items: list, pickup_location_id: str | None):
        """
        Returns:
        {
          fulfillment_location_id,
          allocation_type,
          reasoning (json)
        }
        """

        variant_ids = [i["product_variant_id"] for i in items]

        # ---------- PICKUP ----------
        if order_type == "pickup":
            if not pickup_location_id:
                raise HTTPException(400, "pickup_location_id required")

            ok = AllocationService._location_can_fulfill(
                pickup_location_id, variant_ids
            )

            if not ok:
                raise HTTPException(
                    400,
                    "Selected store cannot fulfill all items"
                )

            return {
                "fulfillment_location_id": pickup_location_id,
                "allocation_type": "store",
                "reasoning": {
                    "policy": "pickup_only",
                    "message": "All items available at selected store"
                },
            }

        # ---------- DELIVERY (warehouse first) ----------
        warehouses = AllocationService._candidate_locations("warehouse")
        for w in warehouses:
            if AllocationService._location_can_fulfill(w["id"], variant_ids):
                return {
                    "fulfillment_location_id": w["id"],
                    "allocation_type": "warehouse",
                    "reasoning": {
                        "policy": "warehouse_first",
                        "message": "All items fulfilled from warehouse",
                        "location": w["name"],
                    },
                }

        # ---------- STORE FALLBACK ----------
        stores = AllocationService._candidate_locations("store")
        for s in stores:
            if AllocationService._location_can_fulfill(s["id"], variant_ids):
                return {
                    "fulfillment_location_id": s["id"],
                    "allocation_type": "store",
                    "reasoning": {
                        "policy": "store_fallback",
                        "message": "Warehouse unavailable, fulfilled from store",
                        "location": s["name"],
                    },
                }

        # ---------- NO SPLIT ----------
        raise HTTPException(
            409,
            "Order cannot be fulfilled from a single location"
        )

    # --------------------------------------------------

    @staticmethod
    def _location_can_fulfill(location_id: str, variant_ids: list) -> bool:
        res = (
            supabase.table("inventory")
            .select("product_variant_id, quantity_on_hand")
            .eq("fulfillment_location_id", location_id)
            .in_("product_variant_id", variant_ids)
            .gt("quantity_on_hand", 0)
            .execute()
        )

        return len(res.data or []) == len(set(variant_ids))

    @staticmethod
    def _candidate_locations(loc_type: str):
        return (
            supabase.table("fulfillment_locations")
            .select("id, name")
            .eq("type", loc_type)
            .eq("is_active", True)
            .execute()
        ).data or []
