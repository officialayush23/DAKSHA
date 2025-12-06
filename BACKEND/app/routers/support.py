from fastapi import APIRouter
from app.models.support import TicketCreate
from app.services.support_service import SupportService

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/tickets")
async def create_ticket(payload: TicketCreate):
    ticket = await SupportService.create_ticket(
        payload.user_id,
        payload.issue_summary,
        payload.conversation_summary,
        payload.sentiment_score,
        payload.order_id,
    )
    return ticket
