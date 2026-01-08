# app/workers/reservation_cleanup.py

import asyncio
import logging
from app.core.database import supabase
logger = logging.getLogger(__name__)

async def reservation_cleanup_loop():
    await asyncio.sleep(10)  # allow app + DNS to settle

    while True:
        try:
            supabase.rpc("release_expired_inventory_reservations").execute()
        except Exception as e:
            logger.warning("Reservation cleanup skipped", exc_info=e)

        await asyncio.sleep(60)

