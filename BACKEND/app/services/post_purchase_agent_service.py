# app/service/post_purchase_agent_service.py
# app/services/post_purchase_agent_service.py
import uuid
from app.services.notification_service import notify_user
from sqlalchemy.orm import Session
from app.models.models import Order, Review
from app.services.telegram_notification_service import send_telegram_and_log
from app.services.support_service import request_return, request_exchange
from app.schemas.schemas import ReturnRequest, ExchangeRequest

async def request_feedback_from_user(db: Session, order_id: uuid.UUID):
    """Tool: Proactively reaches out to the user after delivery to ask for a review."""
    order = db.get(Order, order_id)
    if not order or order.feedback_requested:
        return {"status": "already_requested_or_not_found"}

    order.feedback_requested = True
    db.commit()

    msg = f"⭐ *How was your order?*\nOrder `{str(order_id)[:8]}` was recently delivered! We'd love to know what you think. Reply with a rating (1-5) and your thoughts. If you need a return or exchange, just let me know!"
    
    await notify_user(
    db,
    order.user_id,
    subject="How was your order?",
    message=msg,
    message_type="feedback_request",
    entity_id=order.id
)

    return {"status": "feedback_requested"}

def log_review_from_chat(db: Session, user_id: uuid.UUID, product_id: uuid.UUID, rating: int, comment: str):
    """Tool: Saves a user's review extracted from the chat."""
    review = Review(
        user_id=user_id,
        product_id=product_id,
        rating=rating,
        comment=comment
    )
    db.add(review)
    db.commit()
    return {"status": "review_saved", "review_id": str(review.id)}

def agent_initiate_return(db: Session, user_id: uuid.UUID, order_id: uuid.UUID, variant_id: uuid.UUID, quantity: int, reason: str):
    """Tool: Initiates a return request on behalf of the user from chat."""
    # We reuse the robust logic you already built in support_service!
    payload = ReturnRequest(
        order_id=order_id,
        product_variant_id=variant_id,
        quantity=quantity,
        reason=reason
    )
    ret = request_return(db, user_id, payload)
    return {"status": "return_requested", "return_id": str(ret.id), "return_status": ret.status.value}

def agent_initiate_exchange(db: Session, user_id: uuid.UUID, order_id: uuid.UUID, old_variant_id: uuid.UUID, new_variant_id: uuid.UUID, reason: str):
    """Tool: Initiates an exchange request on behalf of the user from chat."""
    payload = ExchangeRequest(
        order_id=order_id,
        old_variant_id=old_variant_id,
        new_variant_id=new_variant_id,
        reason=reason
    )
    exc = request_exchange(db, user_id, payload)
    return {"status": "exchange_requested", "exchange_id": str(exc.id), "exchange_status": exc.status.value}