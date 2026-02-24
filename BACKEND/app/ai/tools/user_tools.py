import uuid
import json
from langchain.tools import tool
from app.core.database import SessionLocal
from app.services.user_services import get_hydrated_user_profile, get_user_addresses

@tool
def get_user_profile(user_id: str) -> str:
    """Fetches the user's complete profile, preferences, and behavior."""
    with SessionLocal() as db:
        try:
            profile = get_hydrated_user_profile(db, uuid.UUID(user_id))
            return json.dumps(profile)
        except Exception as e:
            return f"Error fetching profile: {str(e)}"

@tool
def get_user_saved_addresses(user_id: str) -> str:
    """Gets saved user addresses for delivery selection."""
    with SessionLocal() as db:
        try:
            addresses = get_user_addresses(db, uuid.UUID(user_id))
            return json.dumps([{"id": str(a.id), "label": a.label, "address": a.address_line1} for a in addresses])
        except Exception as e:
            return f"Error getting addresses: {str(e)}"