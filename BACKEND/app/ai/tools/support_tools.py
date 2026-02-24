# app/ai/tools/support_tools.py
import uuid
import json
from langchain.tools import tool
from sqlalchemy import text
from app.core.database import SessionLocal

# Import your actual services
from app.services.support_service import (
    request_return, get_user_returns, cancel_return,
    request_exchange, get_user_exchanges,
    file_complaint, get_user_complaints,
    request_order_cancellation, get_cancellation_requests
)
from app.schemas.schemas import ReturnRequest, ExchangeRequest, ComplaintCreate

# ==========================================
# LOGGING & HANDOFF UTILS
# ==========================================
def log_agent_event(db, order_id: str, agent_name: str, event_type: str, payload: dict):
    """Safely logs to agent_events table."""
    try:
        db.execute(text("""
            INSERT INTO agent_events (order_id, agent_name, event_type, payload)
            VALUES (:o_id, :a_name, :e_type, CAST(:payload AS jsonb))
        """), {
            "o_id": order_id if order_id else None,
            "a_name": agent_name,
            "e_type": event_type,
            "payload": json.dumps(payload)
        })
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to log event: {e}")

@tool
def request_human_handoff(user_id: str, session_id: str, reason: str, summary: str) -> str:
    """CALL THIS WHEN: The user asks for a human, is angry, or you cannot solve their problem."""
    with SessionLocal() as db:
        try:
            db.execute(text("""
                INSERT INTO agent_handoffs (session_id, user_id, from_agent_name, reason, summary, status)
                VALUES (:s_id, :u_id, 'UnifiedAgent', :reason, :summary, 'open')
            """), {
                "s_id": session_id,
                "u_id": user_id,
                "reason": reason,
                "summary": summary
            })
            db.commit()
            return "Handoff successful. Tell the user a human support agent will review this thread and respond shortly."
        except Exception as e:
            db.rollback()
            return f"Failed to request handoff: {str(e)}"

# ==========================================
# RETURNS
# ==========================================
@tool
def process_return(user_id: str, order_id: str, variant_id: str, quantity: int, reason: str) -> str:
    """Initiates a return for a delivered order."""
    with SessionLocal() as db:
        try:
            payload = ReturnRequest(order_id=uuid.UUID(order_id), product_variant_id=uuid.UUID(variant_id), quantity=quantity, reason=reason)
            ret = request_return(db, uuid.UUID(user_id), payload)
            log_agent_event(db, order_id, "UnifiedAgent", "process_return", {"return_id": str(ret.id), "reason": reason})
            return f"Return requested successfully. ID: {ret.id}."
        except Exception as e:
            return f"Failed to initiate return: {str(e)}"

@tool
def view_returns(user_id: str) -> str:
    """Gets all returns for the user."""
    with SessionLocal() as db:
        try:
            returns = get_user_returns(db, uuid.UUID(user_id))
            data = [{"id": str(r.id), "order_id": str(r.order_id), "status": r.status.value, "reason": r.reason} for r in returns]
            return json.dumps(data)
        except Exception as e:
            return f"Failed to get returns: {str(e)}"

@tool
def cancel_return_request_tool(user_id: str, return_id: str, reason: str = "User requested cancellation") -> str:
    """Cancels a pending return request."""
    with SessionLocal() as db:
        try:
            # Note: Because the service is async, we must run it synchronously here
            import asyncio
            ret = asyncio.run(cancel_return(db, uuid.UUID(return_id), uuid.UUID(user_id), reason))
            return f"Return request {ret.id} successfully cancelled."
        except Exception as e:
            return f"Failed to cancel return: {str(e)}"

# ==========================================
# EXCHANGES
# ==========================================
@tool
def process_exchange(user_id: str, order_id: str, old_variant_id: str, new_variant_id: str, reason: str) -> str:
    """Initiates an exchange for a delivered order."""
    with SessionLocal() as db:
        try:
            payload = ExchangeRequest(order_id=uuid.UUID(order_id), old_variant_id=uuid.UUID(old_variant_id), new_variant_id=uuid.UUID(new_variant_id), reason=reason)
            exc = request_exchange(db, uuid.UUID(user_id), payload)
            log_agent_event(db, order_id, "UnifiedAgent", "process_exchange", {"exchange_id": str(exc.id)})
            return f"Exchange requested successfully. ID: {exc.id}."
        except Exception as e:
            return f"Failed to initiate exchange: {str(e)}"

@tool
def view_exchanges(user_id: str) -> str:
    """Gets all exchanges for the user."""
    with SessionLocal() as db:
        try:
            exchanges = get_user_exchanges(db, uuid.UUID(user_id))
            data = [{"id": str(e.id), "order_id": str(e.order_id), "status": e.status.value} for e in exchanges]
            return json.dumps(data)
        except Exception as e:
            return f"Failed to get exchanges: {str(e)}"

# ==========================================
# ORDER CANCELLATIONS
# ==========================================
@tool
def request_order_cancel(user_id: str, order_id: str, reason: str) -> str:
    """Requests cancellation for an entire order (only works if order is created/confirmed)."""
    with SessionLocal() as db:
        try:
            req = request_order_cancellation(db, uuid.UUID(user_id), uuid.UUID(order_id), reason)
            log_agent_event(db, order_id, "UnifiedAgent", "cancel_order", {"request_id": str(req.id)})
            return f"Order cancellation requested successfully. Status: {req.status.value}."
        except Exception as e:
            return f"Failed to cancel order: {str(e)}"

# ==========================================
# COMPLAINTS
# ==========================================
@tool
def create_complaint(user_id: str, session_id: str, category: str, description: str, order_id: str = None) -> str:
    """Files a formal complaint for the user."""
    with SessionLocal() as db:
        try:
            o_id = uuid.UUID(order_id) if order_id else None
            payload = ComplaintCreate(user_id=uuid.UUID(user_id), order_id=o_id, session_id=uuid.UUID(session_id), category=category, description=description)
            comp = file_complaint(db, uuid.UUID(user_id), payload)
            return f"Complaint filed successfully. Ticket ID: {comp.id}."
        except Exception as e:
            return f"Failed to file complaint: {str(e)}"

@tool
def view_complaints(user_id: str) -> str:
    """Gets all complaints for the user."""
    with SessionLocal() as db:
        try:
            complaints = get_user_complaints(db, uuid.UUID(user_id))
            data = [{"id": str(c.id), "category": c.category, "status": c.status.value, "description": c.description} for c in complaints]
            return json.dumps(data)
        except Exception as e:
            return f"Failed to get complaints: {str(e)}"