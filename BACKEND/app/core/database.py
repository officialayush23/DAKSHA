# app/core/database.py

from supabase import create_client, Client
import redis.asyncio as redis
import json
from app.core.config import settings

# Supabase admin client – SERVICE ROLE key (bypasses RLS)
# Use this for ALL backend operations
# CRITICAL: Must use SERVICE_ROLE_KEY to bypass RLS
supabase_admin: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,
)

# Verify we're using the service role key (not anon key)
# Service role keys typically start with "eyJ" (JWT) and are much longer
if not settings.SUPABASE_SERVICE_ROLE_KEY or len(settings.SUPABASE_SERVICE_ROLE_KEY) < 100:
    raise ValueError(
        "SUPABASE_SERVICE_ROLE_KEY appears invalid. "
        "Service role keys are long JWT tokens. Check your .env file."
    )

# Supabase anon client – ANON key (respects RLS)
# Only use for edge cases that impersonate users
supabase_anon: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY,
)

# Backward compatibility alias (will be deprecated)
# All new code should use supabase_admin
supabase: Client = supabase_admin


class RedisBus:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def publish_json(self, channel: str, event: str, data: dict):
        payload = json.dumps({"event": event, "data": data})
        await self.redis.publish(channel, payload)
    
    async def publish(self, channel: str, message: str):
        """Publish raw message to channel"""
        await self.redis.publish(channel, message)

    async def subscribe(self, channel: str):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub
    
    def pubsub(self):
        """Get pubsub instance for WebSocket subscriptions"""
        return self.redis.pubsub()


redis_client = RedisBus()
