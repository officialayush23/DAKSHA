from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import redis_client
import asyncio

router = APIRouter(tags=["Realtime"])

# ... existing notification/dashboard streams ...

@router.websocket("/ws/store-inventory/{store_id}")
async def store_inventory_stream(websocket: WebSocket, store_id: str):from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import redis_client
import asyncio

router = APIRouter(tags=["Realtime"])


@router.websocket("/ws/store-inventory/{store_id}")
async def store_inventory_stream(websocket: WebSocket, store_id: str):
    """
    Connects the Store Manager's Tablet / Kiosk to live inventory updates.
    """
    await websocket.accept()
    pubsub = await redis_client.subscribe(f"store:{store_id}:inventory")
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if msg:
                await websocket.send_text(msg["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()

    """
    Connects the Store Manager's Tablet / Kiosk to live updates.
    """
    await websocket.accept()
    
    # Subscribe to this specific store's channel
    pubsub = await redis_client.subscribe(f"store:{store_id}:inventory")
    
    try:
        while True:
            # Wait for Redis message
            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if msg:
                # msg['data'] contains the JSON we published in admin_inventory.py
                await websocket.send_text(msg['data'])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()