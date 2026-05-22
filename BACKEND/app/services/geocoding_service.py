# app/services/geocoding_service.py
"""
Google Maps Geocoding + Places API service.

Functions:
  geocode_address(address)         → {"lat": float, "lng": float, "formatted": str}
  reverse_geocode(lat, lng)        → {"formatted": str, "components": dict}
  autocomplete_address(query)      → [{"description": str, "place_id": str}, ...]
  place_details(place_id)          → {"lat": float, "lng": float, "formatted": str}
  nearest_stores_by_coords(...)    → used internally by the store router
"""
import httpx
import logging
from typing import Optional
from app.core.config import settings

log = logging.getLogger(__name__)

_GEOCODE_URL     = "https://maps.googleapis.com/maps/api/geocode/json"
_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
_PLACE_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def _api_key() -> str:
    return settings.GOOGLE_MAPS_API_KEY


# ─────────────────────────────────────────────────────────────────────────────
# GEOCODING  (address → lat/lng)
# ─────────────────────────────────────────────────────────────────────────────

def geocode_address(address: str) -> dict:
    """
    Convert a free-text address to lat/lng.

    Returns:
        {
          "lat": 12.9716,
          "lng": 77.5946,
          "formatted_address": "...",
          "place_id": "..."
        }
    Raises ValueError if the address cannot be resolved.
    """
    params = {
        "address": address,
        "key": _api_key(),
        "region": "in",       # bias results toward India
        "language": "en",
    }
    resp = httpx.get(_GEOCODE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"Geocoding failed for '{address}': {data.get('status')}")

    result = data["results"][0]
    loc = result["geometry"]["location"]
    return {
        "lat": loc["lat"],
        "lng": loc["lng"],
        "formatted_address": result.get("formatted_address", address),
        "place_id": result.get("place_id", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# REVERSE GEOCODING  (lat/lng → address)
# ─────────────────────────────────────────────────────────────────────────────

def reverse_geocode(lat: float, lng: float) -> dict:
    """
    Convert lat/lng to a human-readable address.

    Returns:
        {
          "formatted_address": "...",
          "city": "...",
          "state": "...",
          "pincode": "...",
          "country": "..."
        }
    """
    params = {
        "latlng": f"{lat},{lng}",
        "key": _api_key(),
        "language": "en",
    }
    resp = httpx.get(_GEOCODE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        return {"formatted_address": f"{lat}, {lng}", "city": "", "state": "", "pincode": "", "country": ""}

    result = data["results"][0]
    components = {c["types"][0]: c["long_name"] for c in result.get("address_components", [])}

    return {
        "formatted_address": result.get("formatted_address", ""),
        "city": components.get("locality", components.get("administrative_area_level_2", "")),
        "state": components.get("administrative_area_level_1", ""),
        "pincode": components.get("postal_code", ""),
        "country": components.get("country", ""),
    }


# ─────────────────────────────────────────────────────────────────────────────
# PLACES AUTOCOMPLETE  (partial query → suggestions)
# ─────────────────────────────────────────────────────────────────────────────

def autocomplete_address(query: str, session_token: Optional[str] = None) -> list[dict]:
    """
    Returns up to 5 address suggestions for a partial query.

    Returns:
        [{"description": "...", "place_id": "..."}, ...]
    """
    params = {
        "input": query,
        "key": _api_key(),
        "types": "address",
        "components": "country:in",    # restrict to India
        "language": "en",
    }
    if session_token:
        params["sessiontoken"] = session_token

    resp = httpx.get(_AUTOCOMPLETE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        log.warning("Places autocomplete error: %s", data.get("status"))
        return []

    return [
        {"description": p["description"], "place_id": p["place_id"]}
        for p in data.get("predictions", [])
    ]


# ─────────────────────────────────────────────────────────────────────────────
# PLACE DETAILS  (place_id → lat/lng + full address)
# ─────────────────────────────────────────────────────────────────────────────

def place_details(place_id: str, session_token: Optional[str] = None) -> dict:
    """
    Fetch exact lat/lng + formatted address for a place_id returned by autocomplete.

    Returns:
        {
          "lat": float,
          "lng": float,
          "formatted_address": str,
          "city": str,
          "state": str,
          "pincode": str
        }
    """
    params = {
        "place_id": place_id,
        "fields": "geometry,formatted_address,address_components",
        "key": _api_key(),
        "language": "en",
    }
    if session_token:
        params["sessiontoken"] = session_token

    resp = httpx.get(_PLACE_DETAIL_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK":
        raise ValueError(f"Place details failed for '{place_id}': {data.get('status')}")

    result = data["result"]
    loc = result["geometry"]["location"]
    components = {c["types"][0]: c["long_name"] for c in result.get("address_components", [])}

    return {
        "lat": loc["lat"],
        "lng": loc["lng"],
        "formatted_address": result.get("formatted_address", ""),
        "city": components.get("locality", components.get("administrative_area_level_2", "")),
        "state": components.get("administrative_area_level_1", ""),
        "pincode": components.get("postal_code", ""),
    }
