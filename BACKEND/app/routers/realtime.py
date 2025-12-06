from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import redis_client
from app.core.auth import verify_jwt
import asyncio

router = APIRouter(tags=["Realtime"])


@router.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket, token: str):
    try:
        payload = verify_jwt(token)
        user_id = payload["sub"]
    except Exception:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    pubsub = await redis_client.subscribe(f"user:{user_id}")

    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if msg:
                await websocket.send_text(msg["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()


@router.websocket("/ws/support-dashboard")
async def support_dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    pubsub = await redis_client.subscribe("support:dashboard")
    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if msg:
                await websocket.send_text(msg["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe()


@router.websocket("/ws/store-inventory/{store_id}")
async def store_inventory_ws(websocket: WebSocket, store_id: str):
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
