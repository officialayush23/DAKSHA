from fastapi import HTTPException
from app.database import supabase
from typing import List, Dict, Optional
import math


class AllocationService:
    """
    Allocation policy (authoritative):
    1) Pickup  -> user-selected store only
    2) Delivery:
        a) Warehouse-first (any warehouse that can fully fulfill)
        b) Nearest store fallback (single store only)
    No split allocation (by design).
    """

    # =========================================================
    # PUBLIC API
    # =========================================================
    @staticmethod
    def allocate(
        order_type: str,
        items: List[dict],
        pickup_location_id: Optional[str],
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
    ):
        """
        Returns:
        {
          fulfillment_location_id: uuid,
          allocation_type: "warehouse" | "store",
          reasoning: dict
        }
        """

        if not items:
            raise HTTPException(400, "No items to allocate")

        required_qty = {
            i["product_variant_id"]: int(i["quantity"])
            for i in items
        }

        # --------------------------------------------------
        # PICKUP — STRICT STORE
        # --------------------------------------------------
        if order_type == "pickup":
            if not pickup_location_id:
                raise HTTPException(400, "pickup_location_id required")

            if not AllocationService._location_can_fulfill(
                pickup_location_id, required_qty
            ):
                raise HTTPException(
                    400, "Selected pickup store cannot fulfill all items"
                )

            return {
                "fulfillment_location_id": pickup_location_id,
                "allocation_type": "store",
                "reasoning": {
                    "policy": "pickup_only",
                    "explanation": "User-selected pickup store has sufficient stock",
                },
            }

        # --------------------------------------------------
        # DELIVERY — PHASE 1: WAREHOUSE FIRST
        # --------------------------------------------------
        warehouses = AllocationService._get_locations_by_type("warehouse")

        for wh in warehouses:
            if AllocationService._location_can_fulfill(
                wh["id"], required_qty
            ):
                return {
                    "fulfillment_location_id": wh["id"],
                    "allocation_type": "warehouse",
                    "reasoning": {
                        "policy": "warehouse_first",
                        "warehouse": {
                            "id": wh["id"],
                            "name": wh["name"],
                        },
                        "explanation": "Central warehouse can fulfill entire order",
                    },
                }

        # --------------------------------------------------
        # DELIVERY — PHASE 2: NEAREST STORE FALLBACK
        # --------------------------------------------------
        stores = AllocationService._get_locations_by_type("store")

        candidates = []
        for store in stores:
            if not AllocationService._location_can_fulfill(
                store["id"], required_qty
            ):
                continue

            distance = AllocationService._distance_km(
                user_lat, user_lng, store
            )

            candidates.append({
                "store_id": store["id"],
                "name": store["name"],
                "distance_km": distance,
            })

        if not candidates:
            raise HTTPException(
                409, "Order cannot be fulfilled from a single location"
            )

        candidates.sort(key=lambda x: x["distance_km"])
        winner = candidates[0]

        return {
            "fulfillment_location_id": winner["store_id"],
            "allocation_type": "store",
            "reasoning": {
                "policy": "warehouse_fallback_store",
                "selected_store": winner,
                "alternatives": candidates[1:4],
                "explanation": "No warehouse could fulfill; nearest store selected",
            },
        }

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================
    @staticmethod
    def _location_can_fulfill(
        location_id: str,
        required_qty: Dict[str, int],
    ) -> bool:
        rows = (
            supabase.table("inventory")
            .select("product_variant_id, quantity_on_hand")
            .eq("fulfillment_location_id", location_id)
            .in_("product_variant_id", list(required_qty.keys()))
            .execute()
        ).data or []

        inv_map = {
            r["product_variant_id"]: r["quantity_on_hand"]
            for r in rows
        }

        for variant_id, qty in required_qty.items():
            if inv_map.get(variant_id, 0) < qty:
                return False

        return True

    @staticmethod
    def _get_locations_by_type(loc_type: str):
        return (
            supabase.table("fulfillment_locations")
            .select("id, name, latitude, longitude")
            .eq("type", loc_type)
            .eq("is_active", True)
            .execute()
        ).data or []

    @staticmethod
    def _distance_km(
        user_lat: Optional[float],
        user_lng: Optional[float],
        loc: dict,
    ) -> float:
        if user_lat is None or user_lng is None:
            return float("inf")

        return round(
            AllocationService._haversine(
                user_lat,
                user_lng,
                float(loc["latitude"]),
                float(loc["longitude"]),
            ),
            2,
        )

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(dl / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
