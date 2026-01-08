# app/routers/support.py

from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.schemas.schemas import TicketCreate
from app.services.support_service import SupportService
from app.core.database import supabase
from typing import Optional

router = APIRouter(prefix="/support", tags=["Support"])


@router.get("/tickets")
async def get_user_tickets(user_id: str = Depends(get_current_user_id)):
    """Get all tickets for the current user"""
    try:
        tickets = (
            supabase.table("support_tickets")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        ).data or []
        
        return {"tickets": tickets}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch tickets: {str(e)}")


@router.get("/tickets/{ticket_id}")
async def get_ticket_details(
    ticket_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get specific ticket details"""
    try:
        ticket = (
            supabase.table("support_tickets")
            .select("*")
            .eq("id", ticket_id)
            .eq("user_id", user_id)  # Ensure user can only see their own tickets
            .maybe_single()
            .execute()
        ).data
        
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        
        # Get ticket events
        events = (
            supabase.table("support_ticket_events")
            .select("*")
            .eq("ticket_id", ticket_id)
            .order("created_at", desc=True)
            .execute()
        ).data or []
        
        return {
            "ticket": ticket,
            "events": events
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch ticket: {str(e)}")


@router.post("/tickets")
async def create_ticket(
    payload: TicketCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new support ticket"""
    try:
        ticket = await SupportService.create_ticket(
            user_id=user_id,
            issue_summary=payload.issue_summary,
            conversation_summary=payload.conversation_summary or payload.issue_summary,
            sentiment_score=payload.sentiment_score or 0.5,
            order_id=payload.order_id,
            ticket_type=payload.ticket_type or "general",
            priority=payload.priority or "medium",
        )
        return {"ticket": ticket}
    except Exception as e:
        raise HTTPException(500, f"Failed to create ticket: {str(e)}")


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user_id)
):
    """Update ticket (user can only update their own tickets)"""
    try:
        # Verify ownership
        ticket = (
            supabase.table("support_tickets")
            .select("id")
            .eq("id", ticket_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        ).data
        
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        
        # Update ticket
        updated = (
            supabase.table("support_tickets")
            .update(payload)
            .eq("id", ticket_id)
            .execute()
        ).data
        
        return {"ticket": updated[0] if updated else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to update ticket: {str(e)}")
