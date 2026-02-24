import uuid
import json
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.loyalty_service import get_balance
from app.services.coupon_service import get_eligible_coupons, apply_coupon
from app.services.personalized_offer_service import generate_dynamic_offer
from app.services.user_services import get_user_offers

@tool
def get_loyalty_balance(user_id: str) -> str:
    """Checks the user's loyalty points balance."""
    with SessionLocal() as db:
        try:
            balance = get_balance(db, uuid.UUID(user_id))
            return f"User has {balance} points."
        except Exception as e:
            return f"Error checking balance: {str(e)}"

@tool
def get_checkout_coupons(user_id: str, locked_price: float) -> str:
    """Gets eligible coupons for an active checkout."""
    with SessionLocal() as db:
        try:
            coupons = get_eligible_coupons(db, uuid.UUID(user_id), locked_price, set())
            return json.dumps(coupons)
        except Exception as e:
            return f"Error getting coupons: {str(e)}"

@tool
def apply_discount_code(checkout_id: str, cart_total: float, code: str = None, personal_offer_id: str = None) -> str:
    """Applies a global coupon code OR a personalized offer to an active checkout session."""
    with SessionLocal() as db:
        try:
            discount = apply_coupon(db, uuid.UUID(checkout_id), coupon_code=code, personal_offer_id=personal_offer_id, cart_total=cart_total)
            return f"Success. Applied discount of {discount}."
        except Exception as e:
            return f"Failed to apply coupon: {str(e)}"

@tool
def generate_personalized_offer(user_id: str, session_id: str) -> str:
    """Proactively generates a dynamic, personalized offer for the user based on their behavior."""
    with SessionLocal() as db:
        try:
            offer = generate_dynamic_offer(db, uuid.UUID(user_id))
            return json.dumps({
                "offer_id": str(offer.id),
                "offer_name": offer.offer_name,
                "discount_value": float(offer.discount_value),
                "expires_at": offer.expires_at.isoformat()
            })
        except Exception as e:
            return f"Failed to generate offer: {str(e)}"

@tool
def list_available_offers(user_id: str) -> str:
    """Lists all active, unredeemed personalized offers available to the user."""
    with SessionLocal() as db:
        try:
            offers = get_user_offers(db, uuid.UUID(user_id))
            return json.dumps(offers)
        except Exception as e:
            return f"Failed to fetch offers: {str(e)}"