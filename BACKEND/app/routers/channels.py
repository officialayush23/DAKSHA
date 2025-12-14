# app/routers/channels.py

from fastapi import APIRouter, Depends
from typing import Optional
from app.core.auth import get_current_user_id
from app.models.channels import ChannelMessage
from app.agents.graph import run_sales_agent

router = APIRouter(prefix="/channels", tags=["Omnichannel"])


@router.post("/message")
async def handle_message(
    payload: ChannelMessage,
    user_id: Optional[str] = Depends(get_current_user_id),
):
    reply = await run_sales_agent(
        user_id=user_id,
        channel=payload.channel_type,
        channel_id=payload.channel_id,
        message=payload.message,
    )

    return {"reply": reply}
