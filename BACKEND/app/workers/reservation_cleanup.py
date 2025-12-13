import asyncio
import logging
from app.database import supabase

logger = logging.getLogger("reservation_cleanup")

CLEANUP_INTERVAL_SECONDS = 120  # 2 minutes


async def reservation_cleanup_loop():
    while True:
        try:
            supabase.rpc("release_expired_inventory_reservations").execute()
        except Exception as e:
            logger.exception("Reservation cleanup failed")
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
