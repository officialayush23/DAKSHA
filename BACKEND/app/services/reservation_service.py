# app/services/reservation_service.py
from app.database import supabase
from app.core.redis_bus import EventBus
from fastapi import HTTPException


class ReservationService:

    @staticmethod
    async def release_cart(cart_id: str, reason: str = "expired"):
        reservations = (
            supabase.table("inventory_reservations")
            .select(
                "id, product_variant_id, fulfillment_location_id, quantity"
            )
            .eq("cart_id", cart_id)
            .eq("status", "active")
            .execute()
        ).data or []

        for r in reservations:
            inv = (
                supabase.table("inventory")
                .select(
                    "id, quantity_on_hand, quantity_reserved, version"
                )
                .eq("product_variant_id", r["product_variant_id"])
                .eq(
                    "fulfillment_location_id",
                    r["fulfillment_location_id"],
                )
                .single()
                .execute()
            ).data

            if not inv:
                continue

            updated = (
                supabase.table("inventory")
                .update(
                    {
                        "quantity_on_hand": inv["quantity_on_hand"]
                        + r["quantity"],
                        "quantity_reserved": max(
                            0,
                            inv["quantity_reserved"] - r["quantity"],
                        ),
                        "version": inv["version"] + 1,
                    }
                )
                .eq("id", inv["id"])
                .eq("version", inv["version"])
                .execute()
            ).data

            if not updated:
                continue  # concurrent worker handled it

            supabase.table("inventory_reservations").update(
                {"status": "released"}
            ).eq("id", r["id"]).execute()

            await EventBus.notify_inventory_update(
                r["fulfillment_location_id"],
                {
                    "inventory_id": inv["id"],
                    "product_variant_id": r["product_variant_id"],
                    "quantity_on_hand": updated[0]["quantity_on_hand"],
                    "quantity_reserved": updated[0]["quantity_reserved"],
                    "reason": reason,
                },
            )
