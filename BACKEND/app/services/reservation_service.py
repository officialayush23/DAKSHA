# app/services/reservation_service.py
from app.database import supabase

class ReservationService:

    @staticmethod
    def release_cart(cart_id: str, reason: str = "expired"):
        reservations = (
            supabase.table("inventory_reservations")
            .select("*")
            .eq("cart_id", cart_id)
            .eq("status", "active")
            .execute()
        ).data or []

        for r in reservations:
            # restore inventory
            supabase.table("inventory").update(
                {
                    "quantity_on_hand": supabase.literal(
                        f"quantity_on_hand + {r['quantity']}"
                    ),
                    "quantity_reserved": supabase.literal(
                        f"quantity_reserved - {r['quantity']}"
                    ),
                }
            ).eq(
                "product_variant_id", r["product_variant_id"]
            ).eq(
                "fulfillment_location_id", r["fulfillment_location_id"]
            ).execute()

            # mark reservation released
            supabase.table("inventory_reservations").update(
                {"status": "released"}
            ).eq("id", r["id"]).execute()
