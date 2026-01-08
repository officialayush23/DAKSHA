# app/core/redis_bus.py
import json
from app.core.database import redis_client


class EventBus:
    """
    Centralized realtime event bus.
    All payloads MUST be JSON-serializable.
    Channel naming is CONTRACTUAL with WebSocket consumers.
    """

    # =========================================================
    # INVENTORY (Store / Warehouse / Dark Store)
    # =========================================================

    @staticmethod
    async def notify_inventory_update(
        fulfillment_location_id: str,
        payload: dict,
    ):
        """
        Fired on:
        - quantity change
        - reservation change
        - stock correction
        """
        channel = f"inventory:{fulfillment_location_id}"
        await redis_client.publish(
            channel,
            json.dumps({
                "type": "inventory_update",
                "data": payload,
            })
        )

    @staticmethod
    async def notify_inventory_alert(
        fulfillment_location_id: str,
        alert: dict,
    ):
        """
        Fired on:
        - low stock
        - zero stock
        - negative drift
        - reconciliation failures
        """
        channel = f"inventory:{fulfillment_location_id}:alerts"
        await redis_client.publish(
            channel,
            json.dumps({
                "type": "inventory_alert",
                "data": alert,
            })
        )

    # =========================================================
    # SUPPORT DASHBOARD
    # =========================================================

    @staticmethod
    async def notify_support_dashboard(
        event: str,
        payload: dict,
    ):
        """
        Fired on:
        - new ticket
        - ticket update
        - SLA breach
        """
        await redis_client.publish(
            "support_dashboard",
            json.dumps({
                "event": event,
                "data": payload,
            })
        )
