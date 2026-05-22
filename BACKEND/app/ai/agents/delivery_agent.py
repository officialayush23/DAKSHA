# app/ai/agents/delivery_agent.py
"""
DeliveryAgent — Groq llama-3.3-70b
Handles tracking, delays, reschedules, delivery exceptions, pickup status.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from typing import Optional
from app.ai.llm import get_llm_for_agent
from app.ai.message_utils import trim_messages_for_groq
from app.ai.state import AgentState
from app.ai.policy.company_policy import build_agent_prompt
from app.ai.tools.inventory_tools import agent_reschedule_delivery, find_nearest_pickup_stores
from app.core.database import SessionLocal
from app.models.models import Order, DeliveryTracking, RescheduleRequest
import uuid


# ── New tools for DeliveryAgent ───────────────────────────────────────────────

@tool
def get_order_tracking(order_id: str, user_id: str) -> dict:
    """
    Get the latest delivery tracking events for an order.
    Returns a list of tracking events sorted by most recent first.
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.id == uuid.UUID(order_id),
        ).first()
        if not order:
            return {"error": "Order not found."}

        events = db.query(DeliveryTracking).filter(
            DeliveryTracking.order_id == uuid.UUID(order_id)
        ).order_by(DeliveryTracking.recorded_at.desc()).limit(10).all()

        return {
            "order_id": order_id,
            "order_status": order.status.value if order.status else "unknown",
            "estimated_delivery_date": str(order.estimated_delivery_date) if order.estimated_delivery_date else None,
            "last_tracking_status": order.last_tracking_status,
            "is_exception": order.is_delivery_exception,
            "tracking_events": [
                {
                    "status": e.status,
                    "location": e.location_text,
                    "message": e.carrier_message,
                    "is_exception": e.is_exception,
                    "recorded_at": str(e.recorded_at),
                }
                for e in events
            ],
        }
    finally:
        db.close()


@tool
def request_reschedule(order_id: str, user_id: str, reason: Optional[str] = None) -> dict:
    """
    Create a reschedule request for a delivery. Returns available time slots.
    The user will then choose a slot via a follow-up message.
    """
    from datetime import datetime, timedelta
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == uuid.UUID(order_id)).first()
        if not order:
            return {"error": "Order not found."}
        if order.status.value in ("delivered", "cancelled"):
            return {"error": f"Cannot reschedule — order is already {order.status.value}."}

        # Generate 3 available slots (tomorrow + 2 days after)
        base = datetime.now()
        slots = [
            (base + timedelta(days=i)).replace(hour=10, minute=0, second=0).isoformat()
            for i in range(1, 4)
        ]
        rr = RescheduleRequest(
            order_id=uuid.UUID(order_id),
            requested_by="user",
            offered_slots=slots,
            reason=reason,
            status="pending",
        )
        db.add(rr)
        db.commit()
        db.refresh(rr)

        return {
            "reschedule_request_id": str(rr.id),
            "available_slots": slots,
            "message": "Reschedule request created. Please choose one of the slots above.",
        }
    finally:
        db.close()


@tool
def confirm_reschedule_slot(reschedule_request_id: str, chosen_slot: str) -> dict:
    """
    Confirm the user's chosen delivery slot for an existing reschedule request.
    """
    db = SessionLocal()
    try:
        from datetime import datetime
        rr = db.query(RescheduleRequest).filter(
            RescheduleRequest.id == uuid.UUID(reschedule_request_id)
        ).first()
        if not rr:
            return {"error": "Reschedule request not found."}
        if rr.status != "pending":
            return {"error": f"Request is already {rr.status}."}

        rr.chosen_slot = datetime.fromisoformat(chosen_slot)
        rr.status = "user_selected"
        db.commit()
        return {
            "success": True,
            "message": f"Delivery rescheduled to {chosen_slot}. You'll receive a confirmation email shortly.",
        }
    finally:
        db.close()


@tool
def report_delivery_issue(order_id: str, user_id: str, issue_description: str) -> dict:
    """
    Report a delivery issue (not received, damaged, wrong address etc.)
    Creates a complaint record linked to the order.
    """
    db = SessionLocal()
    try:
        from app.models.models import Complaint
        from app.enums.db_enums import ComplaintStatusEnum
        order = db.query(Order).filter(Order.id == uuid.UUID(order_id)).first()
        if not order:
            return {"error": "Order not found."}

        complaint = Complaint(
            user_id=uuid.UUID(user_id),
            order_id=uuid.UUID(order_id),
            subject="Delivery Issue",
            description=issue_description,
            status=ComplaintStatusEnum.open,
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        return {
            "complaint_id": str(complaint.id),
            "message": "Your delivery issue has been logged. Our team will reach out within 24 hours.",
        }
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


# ── Agent definition ──────────────────────────────────────────────────────────

DELIVERY_INSTRUCTIONS = """
You handle all delivery-related queries: tracking, delays, rescheduling, exceptions.

CAPABILITIES:
  • get_order_tracking        — show live tracking events for an order
  • request_reschedule        — create a reschedule request (shows available slots)
  • confirm_reschedule_slot   — confirm the user's chosen slot
  • report_delivery_issue     — log a delivery problem (not received, damaged etc.)
  • agent_reschedule_delivery — internal reschedule trigger for automated retries
  • find_nearest_pickup_stores — if user wants to switch to store pickup

RULES:
1. Always call get_order_tracking first before any reschedule or issue report.
2. After showing tracking, offer proactive help: "Would you like to reschedule or report an issue?"
3. For reschedule, first show slots, THEN wait for user to choose, THEN call confirm_reschedule_slot.
4. If delivery attempt count ≥ 3 AND order is not delivered, escalate to Handoff.
5. If user reports missing delivery AND it's been > 7 days past EDD, escalate to Handoff.
6. Always wrap tracking data in <UI_DATA> ... </UI_DATA> tags.
7. Be empathetic — delivery issues are stressful.

User ID: {user_id}
Session ID: {session_id}
"""

delivery_tools = [
    get_order_tracking,
    request_reschedule,
    confirm_reschedule_slot,
    report_delivery_issue,
    agent_reschedule_delivery,
    find_nearest_pickup_stores,
]

_llm = get_llm_for_agent("DeliveryAgent").bind_tools(delivery_tools)
_llm_text = get_llm_for_agent("DeliveryAgent")

_prompt = ChatPromptTemplate.from_messages([
    ("system", build_agent_prompt("Delivery Agent", DELIVERY_INSTRUCTIONS)),
    MessagesPlaceholder(variable_name="messages"),
])

_chain = _prompt | _llm
_chain_text = _prompt | _llm_text


def delivery_agent_node(state: AgentState) -> dict:
    messages = trim_messages_for_groq(state["messages"])
    ctx = {
        "messages": messages,
        "user_id": state.get("user_id", ""),
        "session_id": state.get("session_id", ""),
    }
    if messages and isinstance(messages[-1], ToolMessage):
        response = _chain_text.invoke(ctx)
    else:
        response = _chain.invoke(ctx)
    return {"messages": [response], "current_agent": "DeliveryAgent"}
