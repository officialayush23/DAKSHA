import re
from datetime import date, datetime
from fastapi import HTTPException
from postgrest.exceptions import APIError
from app.database import supabase

# DB constraint: ^\+[1-9]\d{1,14}$ -> "+" + 1–15 digits (total length 2–16)
PHONE_REGEX = re.compile(r'^\+[1-9]\d{1,14}$')


def _normalize_phone(phone: str | None) -> str | None:
  """
  Normalize phone to be DB-safe:

  - Accepts things like "+91 95294-19952"
  - Strips spaces & dashes
  - Returns None for empty
  - Enforces E.164 pattern before DB sees it
  """
  if phone is None:
    return None

  raw = phone.strip()
  if raw == "":
    return None

  # Allow user to type spaces/hyphens but kill them
  if not raw.startswith("+"):
    # Force them to put the "+" correctly – don't guess country code
    raise HTTPException(
      400,
      f"Invalid phone number format: '{phone}'. Must start with '+' (e.g., +919876543210).",
    )

  # Remove everything except digits after the "+"
  digits_only = re.sub(r"\D", "", raw[1:])
  normalized = f"+{digits_only}"

  if not PHONE_REGEX.match(normalized):
    raise HTTPException(
      400,
      f"Invalid phone number format: '{phone}'. Use E.164 like +919876543210 (no spaces).",
    )

  return normalized


class UserService:
  @staticmethod
  async def ensure_user_exists(user_id: str) -> dict:
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    if res.data:
      return res.data[0]

    new_profile = {
      "id": user_id,
      "is_active": True,
    }
    created = supabase.table("users").insert(new_profile).execute()
    if not created.data:
      raise HTTPException(500, "Failed to create user profile")
    return created.data[0]

  @staticmethod
  async def update_profile(user_id: str, data: dict) -> dict:
    # 1) Normalize empty strings → None
    normalized_data: dict = {}
    for k, v in data.items():
      if v == "" or v is None:
        normalized_data[k] = None
      else:
        normalized_data[k] = v

    # 2) Normalize + validate phone if present
    if "phone_number" in normalized_data:
      normalized_data["phone_number"] = _normalize_phone(
        normalized_data["phone_number"]
      )

      # Uniqueness check only on active users (matches partial index)
      if normalized_data["phone_number"]:
        check = (
          supabase.table("users")
          .select("id")
          .eq("phone_number", normalized_data["phone_number"])
          .eq("is_active", True)
          .neq("id", user_id)
          .execute()
        )
        if check.data:
          raise HTTPException(
            400, "Phone number already in use by another active user"
          )

    # 3) Dates → ISO strings
    payload: dict = {}
    for k, v in normalized_data.items():
      if isinstance(v, (date, datetime)):
        payload[k] = v.isoformat()
      else:
        payload[k] = v

    # 4) Nothing to update? Just return current profile
    if not payload:
      res = supabase.table("users").select("*").eq("id", user_id).execute()
      if not res.data:
        raise HTTPException(404, "User not found")
      return res.data[0]

    # 5) Supabase update with nice error mapping
    try:
      res = supabase.table("users").update(payload).eq("id", user_id).execute()
      if not res.data:
        raise HTTPException(404, "User not found")
      return res.data[0]

    except APIError as e:
      error_code = e.code or ""
      error_message = e.message or str(e)
      error_details = (e.details or "").lower()

      if "chk_phone_format" in error_details or "pgrst116" in error_code:
        raise HTTPException(
          400,
          "Invalid phone number format. Must be E.164 (e.g., +911234567890).",
        )
      elif (
        "idx_users_active_phone" in error_details
        or "23505" in error_code
        or "unique" in error_details
      ):
        raise HTTPException(
          400, "Phone number already in use by another active user"
        )
      elif "23514" in error_code or "check constraint" in error_details:
        raise HTTPException(400, f"Validation error: {error_message}")
      else:
        raise HTTPException(
          500, f"Database error: {error_message} (code: {error_code})"
        )

    except Exception as e:
      raise HTTPException(500, f"Unexpected error: {str(e)}")

  @staticmethod
  async def add_payment_method(user_id: str, token_id: str, last4: str, brand: str):
    supabase.table("user_payment_methods").update(
      {"is_default": False}
    ).eq("user_id", user_id).execute()

    res = supabase.table("user_payment_methods").insert(
      {
        "user_id": user_id,
        "provider": "razorpay",
        "gateway_token_id": token_id,
        "card_last4": last4,
        "card_brand": brand,
        "is_default": True,
      }
    ).execute()

    if not res.data:
      raise HTTPException(500, "Failed to save payment method")
    return res.data[0]
