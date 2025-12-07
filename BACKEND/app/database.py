import json
import redis.asyncio as redis
from supabase import create_client, Client
from app.config import settings


supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,   
)


class RedisBus:
    def __init__(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )

    async def publish_json(self, channel: str, event: str, data: dict):
        """
        Publish JSON payload to a Redis pub/sub channel.
        """
        payload = json.dumps({
            "event": event,
            "data": data
        })
        await self.redis.publish(channel, payload)

    async def subscribe(self, channel: str):
        """
        Subscribe to a Redis pub/sub channel.
        """
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

redis_client = RedisBus()
