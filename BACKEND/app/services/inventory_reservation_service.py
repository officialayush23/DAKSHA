# app/services/inventory_reservation_service.py

from datetime import datetime
from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus
import logging

logger = logging.getLogger("daksha.reservations")


class InventoryReservationService:
    """
    Releases expired inventory reservations safely.
    """

    @staticmethod
    async def release_expired_reservations(batch_size: int = 100):
        now = datetime.utcnow()

        # 1) Fetch expired active reservations
        res = (
            supabase.table("inventory_reservations")
            .select(
                "id, product_variant_id, fulfillment_location_id, quantity"
            )
            .eq("status", "active")
            .lt("expires_at", now.isoformat())
            .limit(batch_size)
            .execute()
        )

        reservations = res.data or []
        if not reservations:
            return 0

        released_count = 0

        for r in reservations:
            try:
                InventoryReservationService._release_single(r)
                released_count += 1
            except Exception:
                logger.exception(
                    f"Failed releasing reservation {r['id']}"
                )

        return released_count

    @staticmethod
    def _release_single(reservation: dict):
        """
        Atomic release:
        - decrement quantity_reserved
        - increment quantity_on_hand
        - mark reservation as released
        """

        # 2) Fetch inventory row
        inv = (
            supabase.table("inventory")
            .select("id, quantity_on_hand, quantity_reserved, version")
            .eq("product_variant_id", reservation["product_variant_id"])
            .eq(
                "fulfillment_location_id",
                reservation["fulfillment_location_id"],
            )
            .single()
            .execute()
        ).data

        if not inv:
            raise HTTPException(500, "Inventory row missing")

        # 3) Optimistic update
        updated = (
            supabase.table("inventory")
            .update(
                {
                    "quantity_on_hand": inv["quantity_on_hand"]
                    + reservation["quantity"],
                    "quantity_reserved": max(
                        0,
                        inv["quantity_reserved"] - reservation["quantity"],
                    ),
                    "version": inv["version"] + 1,
                }
            )
            .eq("id", inv["id"])
            .eq("version", inv["version"])
            .execute()
        ).data

        if not updated:
            # Another worker beat us → safe skip
            return

        # 4) Mark reservation released
        supabase.table("inventory_reservations").update(
            {"status": "released"}
        ).eq("id", reservation["id"]).execute()

        # 5) Realtime push
        EventBus.notify_inventory_update(
            reservation["fulfillment_location_id"],
            {
                "inventory_id": inv["id"],
                "product_variant_id": reservation["product_variant_id"],
                "quantity_on_hand": updated[0]["quantity_on_hand"],
                "quantity_reserved": updated[0]["quantity_reserved"],
                "reason": "reservation_expired",
            },
        )
