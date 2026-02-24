# app/ai/tools/loyalty_tools.py
import uuid
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.loyalty_service import get_balance
from app.services.coupon_service import get_eligible_coupons, apply_coupon

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
def apply_discount_code(checkout_id: str, cart_total: float, code: str = None, personal_offer_id: str = None) -> str:
    """Applies a global coupon code OR a personalized offer to an active checkout session."""
    with SessionLocal() as db:
        try:
            discount = apply_coupon(db, checkout_id=uuid.UUID(checkout_id), coupon_code=code, personal_offer_id=personal_offer_id, cart_total=cart_total)
            return f"Success. Applied discount of {discount}."
        except Exception as e:
            return f"Failed to apply coupon: {str(e)}"
        
        
# need to add tool of generating personalized offers and commit to db and a tool to list all offers available to the user,all services are available.