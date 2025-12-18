# # app/routers/channels.py

# from fastapi import APIRouter, Depends
# from typing import Optional
# from app.core.auth import get_current_user_id
# from app.models.channels import ChannelMessage
# from app.agents.graph import run_sales_agent

# router = APIRouter(prefix="/channels", tags=["Omnichannel"])

# @router.post("/message")
# async def handle_message(
#     payload: ChannelMessage,
#     user_id: Optional[str] = Depends(get_current_user_id),
# ):
#     # 🛠️ FIX: Map friendly names to DB Enum values
#     # DB Enum: web_cookie, app_device_id, whatsapp, kiosk_device_id, email
#     db_channel = payload.channel_type
#     if payload.channel_type == "web":
#         db_channel = "web_cookie"
#     elif payload.channel_type == "app":
#         db_channel = "app_device_id"
#     elif payload.channel_type == "kiosk":
#         db_channel = "kiosk_device_id"

#     reply = await run_sales_agent(
#         user_id=user_id,
#         channel=db_channel,  # Pass the corrected enum to the agent/service
#         channel_id=payload.channel_id,
#         message=payload.message,
#     )

#     return {"reply": reply}
