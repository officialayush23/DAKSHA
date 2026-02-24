# app/ai/tools/support_tools.py
import uuid
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.support_service import request_return, request_exchange, file_complaint
from app.schemas.schemas import ReturnRequest, ExchangeRequest, ComplaintCreate

@tool
def process_return(user_id: str, order_id: str, variant_id: str, quantity: int, reason: str) -> str:
    """Initiates a return for a delivered order."""
    with SessionLocal() as db:
        try:
            payload = ReturnRequest(order_id=uuid.UUID(order_id), product_variant_id=uuid.UUID(variant_id), quantity=quantity, reason=reason)
            ret = request_return(db, uuid.UUID(user_id), payload)
            return f"Return requested successfully. ID: {ret.id}."
        except Exception as e:
            return f"Failed to initiate return: {str(e)}"

@tool
def process_exchange(user_id: str, order_id: str, old_variant_id: str, new_variant_id: str, reason: str) -> str:
    """Initiates an exchange for a delivered order."""
    with SessionLocal() as db:
        try:
            payload = ExchangeRequest(order_id=uuid.UUID(order_id), old_variant_id=uuid.UUID(old_variant_id), new_variant_id=uuid.UUID(new_variant_id), reason=reason)
            exc = request_exchange(db, uuid.UUID(user_id), payload)
            return f"Exchange requested successfully. ID: {exc.id}."
        except Exception as e:
            return f"Failed to initiate exchange: {str(e)}"
            
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
        
        
        
        
# need to add the get status of the returns , show all returns , same for exchange and complaint.