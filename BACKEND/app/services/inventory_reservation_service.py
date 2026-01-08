# app/services/inventory_reservation_service.py

from datetime import datetime
from fastapi import HTTPException
from app.core.database import supabase
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
        Release reservation using RPC.
        """
        from app.core.rpc import RPCService
        
        # Use RPC to release reservation
        RPCService.release_inventory_reservation(reservation["id"])
        
        # Realtime push (read current state after release)
        inv = (
            supabase.table("inventory")
            .select("id, quantity_on_hand, quantity_reserved")
            .eq("product_variant_id", reservation["product_variant_id"])
            .eq("fulfillment_location_id", reservation["fulfillment_location_id"])
            .maybe_single()
            .execute()
        ).data
        
        if inv:
            EventBus.notify_inventory_update(
                reservation["fulfillment_location_id"],
                {
                    "inventory_id": inv["id"],
                    "product_variant_id": reservation["product_variant_id"],
                    "quantity_on_hand": inv["quantity_on_hand"],
                    "quantity_reserved": inv.get("quantity_reserved", 0),
                    "reason": "reservation_expired",
                },
            )
