# app/services/inventory_service.py

from fastapi import HTTPException
from app.core.database import supabase
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
