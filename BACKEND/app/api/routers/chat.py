# app/api/routers/chat.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.services.agent_service import run_omnichannel_agent
from app.services.conversation_summary_service import update_conversation_summary

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/message")
async def chat_message(
    message: str,
    channel: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    response = await run_omnichannel_agent(
        db=db,
        user_id=user.id,
        session_id=None,
        message=message,
        channel=channel
    )
    
    update_conversation_summary(db, user.sessions[-1].id)

    
    return {"reply": response}
