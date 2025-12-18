# app/routers/realtime.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import redis_client
import asyncio

router = APIRouter(tags=["Realtime"])


@router.websocket("/ws/inventory/{fulfillment_location_id}")
async def inventory_stream(websocket: WebSocket, fulfillment_location_id: str):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(
        f"inventory:{fulfillment_location_id}",
        f"inventory_alerts:{fulfillment_location_id}",
    )

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0
            )
            if message:
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        await pubsub.unsubscribe()
    finally:
        await pubsub.close()



@router.websocket("/ws/inventory-alerts/{fulfillment_location_id}")
async def inventory_alert_stream(websocket: WebSocket, fulfillment_location_id: str):
    await websocket.accept()
    pubsub = await redis_client.subscribe(
        f"inventory:{fulfillment_location_id}:alerts"
    )

    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if msg:
                await websocket.send_text(msg["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()


@router.websocket("/ws/notifications/{user_id}")
async def notification_stream(websocket: WebSocket, user_id: str):
    await websocket.accept()
    # Subscribe to user-specific channel
    pubsub = await redis_client.subscribe(f"user:{user_id}:notifications")
    
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if msg:
                await websocket.send_text(msg["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()