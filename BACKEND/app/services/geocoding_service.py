# app/services/geocoding_service.py
"""
Geocoding on Mapbox (Google Maps billing is off for this project).

  geocode_address(address)       -> {"lat","lng","formatted_address","place_id"}
  reverse_geocode(lat, lng)      -> {"formatted_address","city","state","pincode","country"}
  autocomplete_address(query)    -> [{"description","place_id"}]   (Search Box /suggest)
  place_details(place_id)        -> {"lat","lng","formatted_address","city","state","pincode"} (/retrieve)

The function names and return shapes are unchanged, so the stores router and
admin UI keep working. Uses MAP_BOX_API_KEY (secret) or MAPBOX_TOKEN (public).
"""
import logging
import uuid
from typing import Optional

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_FWD = "https://api.mapbox.com/search/geocode/v6/forward"
_REV = "https://api.mapbox.com/search/geocode/v6/reverse"
_SUGGEST = "https://api.mapbox.com/search/searchbox/v1/suggest"
_RETRIEVE = "https://api.mapbox.com/search/searchbox/v1/retrieve/{id}"


def _token() -> str:
    tok = (settings.MAP_BOX_API_KEY or settings.MAPBOX_TOKEN or "").strip().strip('"')
    if not tok:
        raise ValueError("Mapbox token missing: set MAP_BOX_API_KEY or MAPBOX_TOKEN")
    return tok


def _ctx(props: dict) -> dict:
    c = props.get("context", {}) or {}
    return {
        "city": (c.get("place") or c.get("locality") or c.get("district") or {}).get("name", ""),
        "state": (c.get("region") or {}).get("name", ""),
        "pincode": (c.get("postcode") or {}).get("name", ""),
        "country": (c.get("country") or {}).get("name", ""),
    }


def geocode_address(address: str) -> dict:
    r = httpx.get(_FWD, params={"q": address, "country": "in", "limit": 1, "language": "en",
                                "access_token": _token()}, timeout=10)
    r.raise_for_status()
    feats = r.json().get("features") or []
    if not feats:
        raise ValueError(f"Geocoding failed for '{address}': no match")
    f = feats[0]
    lng, lat = f["geometry"]["coordinates"]
    p = f.get("properties", {})
    return {"lat": lat, "lng": lng,
            "formatted_address": p.get("full_address") or p.get("name") or address,
            "place_id": p.get("mapbox_id", "")}


def reverse_geocode(lat: float, lng: float) -> dict:
    try:
        r = httpx.get(_REV, params={"longitude": lng, "latitude": lat, "limit": 1, "language": "en",
                                    "access_token": _token()}, timeout=10)
        r.raise_for_status()
        feats = r.json().get("features") or []
    except Exception as e:
        log.warning("reverse geocode failed: %s", e)
        feats = []
    if not feats:
        return {"formatted_address": f"{lat}, {lng}", "city": "", "state": "", "pincode": "", "country": ""}
    p = feats[0].get("properties", {})
    return {"formatted_address": p.get("full_address") or p.get("name", ""), **_ctx(p)}


def autocomplete_address(query: str, session_token: Optional[str] = None) -> list[dict]:
    try:
        r = httpx.get(_SUGGEST, params={"q": query, "country": "in", "limit": 5, "language": "en",
                                        "session_token": session_token or str(uuid.uuid4()),
                                        "access_token": _token()}, timeout=10)
        r.raise_for_status()
    except Exception as e:
        log.warning("Mapbox suggest error: %s", e)
        return []
    out = []
    for s in r.json().get("suggestions", []):
        desc = ", ".join(x for x in [s.get("name"), s.get("place_formatted")] if x)
        out.append({"description": desc or s.get("full_address", ""), "place_id": s.get("mapbox_id")})
    return out


def place_details(place_id: str, session_token: Optional[str] = None) -> dict:
    r = httpx.get(_RETRIEVE.format(id=place_id),
                  params={"session_token": session_token or str(uuid.uuid4()), "access_token": _token()}, timeout=10)
    r.raise_for_status()
    feats = r.json().get("features") or []
    if not feats:
        raise ValueError(f"Place details failed for '{place_id}'")
    f = feats[0]
    lng, lat = f["geometry"]["coordinates"]
    p = f.get("properties", {})
    ctx = _ctx(p)
    return {"lat": lat, "lng": lng,
            "formatted_address": p.get("full_address") or ", ".join(x for x in [p.get("name"), p.get("place_formatted")] if x),
            "city": ctx["city"], "state": ctx["state"], "pincode": ctx["pincode"]}
