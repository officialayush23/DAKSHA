from app.database import redis_client


class EventBus:
    """
    Semantic Redis channels:
      user:{user_id}             -> notifications, order status, etc.
      store:{store_id}:inventory -> store inventory dashboards
      support:dashboard          -> support/complaints dashboard
    """

    @staticmethod
    async def notify_user(user_id: str, event: str, data: dict):
        await redis_client.publish_json(f"user:{user_id}", event, data)

    @staticmethod
    async def notify_store_inventory(store_id: str, data: dict):
        await redis_client.publish_json(
            f"store:{store_id}:inventory",
            "inventory_update",
            data,
        )

    @staticmethod
    async def notify_support_dashboard(event: str, data: dict):
        await redis_client.publish_json("support:dashboard", event, data)
