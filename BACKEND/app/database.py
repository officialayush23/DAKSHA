from supabase import create_client, Client
import redis.asyncio as redis
import json
from app.config import settings

# Supabase client – service role key for backend
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,
)

class RedisBus:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def publish_json(self, channel: str, event: str, data: dict):
        payload = json.dumps({"event": event, "data": data})
        await self.redis.publish(channel, payload)

    async def subscribe(self, channel: str):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

redis_client = RedisBus()
