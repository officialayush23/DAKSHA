# app/api/routers/stores.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from pydantic import BaseModel
import uuid

from app.core.deps import get_db, get_current_user
from app.schemas.schemas import StoreLookupRequest
from app.services.store_availability_service import get_nearest_stores_with_cart
from app.services.geocoding_service import (
    geocode_address,
    reverse_geocode,
    autocomplete_address,
    place_details,
)
from app.models.models import Store, User

router = APIRouter(prefix="/stores", tags=["Stores"])


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class StoreCreateRequest(BaseModel):
    name: str
    address: str                          # full human address — auto-geocoded
    city: str = ""
    state: str = ""
    active: bool = True
    # Optional manual override — if provided, skip geocoding
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class StoreUpdateRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    active: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class GeocodeRequest(BaseModel):
    address: str
    session_token: Optional[str] = None

class PlaceDetailRequest(BaseModel):
    place_id: str
    session_token: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# GEOCODING HELPERS  (frontend calls these for live autocomplete)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/geocode/autocomplete")
def address_autocomplete(
    q: str = Query(..., min_length=2, description="Partial address query"),
    session_token: Optional[str] = Query(None),
    _: User = Depends(get_current_user),
):
    """
    Returns up to 5 Google Places autocomplete suggestions.
    Use session_token (UUID string) to group autocomplete + detail calls for billing.
    """
    try:
        return autocomplete_address(q, session_token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Places API error: {e}")


@router.post("/geocode/place")
def get_place_detail(
    body: PlaceDetailRequest,
    _: User = Depends(get_current_user),
):
    """Resolves a place_id (from autocomplete) to exact lat/lng + address components."""
    try:
        return place_details(body.place_id, body.session_token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Place detail error: {e}")


@router.post("/geocode/address")
def geocode(
    body: GeocodeRequest,
    _: User = Depends(get_current_user),
):
    """Free-text address → lat/lng (single geocoding call, no session)."""
    try:
        return geocode_address(body.address)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Geocoding error: {e}")


@router.get("/geocode/reverse")
def reverse(
    lat: float = Query(...),
    lng: float = Query(...),
    _: User = Depends(get_current_user),
):
    """lat/lng → human-readable address."""
    try:
        return reverse_geocode(lat, lng)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reverse geocoding error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STORE PICKUP QUERIES  (user-facing checkout flow)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/nearest")
def nearest(data: StoreLookupRequest, db: Session = Depends(get_db)):
    return get_nearest_stores_with_cart(db, data.cart_id, data.latitude, data.longitude)


@router.get("/nearby")
def nearby_stores(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(20.0, description="Search radius in kilometres"),
    db: Session = Depends(get_db),
):
    """
    Returns stores near (lat, lng) within radius_km, ordered by distance.
    Used by the Google Maps store picker in the frontend pickup checkout flow.
    Each store includes available_stock (sum across all variants in the area).
    """
    sql = text("""
        SELECT
            s.id,
            s.name,
            s.address,
            s.city,
            s.state,
            ST_Y(s.location::geometry)  AS latitude,
            ST_X(s.location::geometry)  AS longitude,
            ROUND(
                ST_Distance(s.location, ST_MakePoint(:lng, :lat)::geography) / 1000.0,
                2
            )::float                    AS distance_km,
            COALESCE(SUM(si.quantity), 0)::int AS available_stock
        FROM stores s
        LEFT JOIN store_inventory si ON si.store_id = s.id AND si.quantity > 0
        WHERE s.location IS NOT NULL
          AND s.active = true
          AND ST_DWithin(
              s.location,
              ST_MakePoint(:lng, :lat)::geography,
              :radius_m
          )
        GROUP BY s.id, s.name, s.address, s.city, s.state, s.location
        ORDER BY distance_km ASC
        LIMIT 20
    """)

    rows = db.execute(sql, {
        "lat": lat,
        "lng": lng,
        "radius_m": radius_km * 1000,
    }).mappings().all()

    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN — CRUD STORE MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/admin/list")
def admin_list_stores(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all stores (admin)."""
    sql = text("""
        SELECT
            s.id, s.name, s.address, s.city, s.state, s.active,
            ST_Y(s.location::geometry) AS latitude,
            ST_X(s.location::geometry) AS longitude
        FROM stores s
        ORDER BY s.name ASC
    """)
    rows = db.execute(sql).mappings().all()
    return [dict(r) for r in rows]


@router.post("/admin/create")
def admin_create_store(
    body: StoreCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Create a new store. If lat/lng are not provided, the address is
    automatically geocoded via Google Maps Geocoding API.
    """
    lat, lng, formatted = body.latitude, body.longitude, body.address
    city, state = body.city, body.state

    if lat is None or lng is None:
        try:
            geo = geocode_address(body.address)
            lat = geo["lat"]
            lng = geo["lng"]
            formatted = geo["formatted_address"]
            # Auto-fill city/state if not provided
            if not city or not state:
                rev = reverse_geocode(lat, lng)
                city = city or rev.get("city", "")
                state = state or rev.get("state", "")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not geocode address: {e}")

    # Insert with PostGIS geography point
    sql = text("""
        INSERT INTO stores (id, name, address, city, state, active, location)
        VALUES (
            gen_random_uuid(),
            :name,
            :address,
            :city,
            :state,
            :active,
            ST_MakePoint(:lng, :lat)::geography
        )
        RETURNING
            id, name, address, city, state, active,
            ST_Y(location::geometry) AS latitude,
            ST_X(location::geometry) AS longitude
    """)
    row = db.execute(sql, {
        "name": body.name,
        "address": formatted,
        "city": city,
        "state": state,
        "active": body.active,
        "lat": lat,
        "lng": lng,
    }).mappings().first()
    db.commit()
    return dict(row)


@router.put("/admin/{store_id}")
def admin_update_store(
    store_id: str,
    body: StoreUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update an existing store. Re-geocodes if address changed but lat/lng not provided."""
    # Fetch current row
    current = db.execute(
        text("SELECT * FROM stores WHERE id = :id"),
        {"id": store_id}
    ).mappings().first()
    if not current:
        raise HTTPException(status_code=404, detail="Store not found")

    # Determine final lat/lng
    lat = body.latitude
    lng = body.longitude
    address = body.address or current["address"]

    # Re-geocode only if address changed and no manual coords given
    if body.address and body.address != current["address"] and lat is None:
        try:
            geo = geocode_address(body.address)
            lat = geo["lat"]
            lng = geo["lng"]
            address = geo["formatted_address"]
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not geocode address: {e}")

    # Build partial update
    updates = {}
    if body.name is not None:      updates["name"] = body.name
    if body.city is not None:      updates["city"] = body.city
    if body.state is not None:     updates["state"] = body.state
    if body.active is not None:    updates["active"] = body.active
    updates["address"] = address

    set_clauses = [f"{k} = :{k}" for k in updates]

    if lat is not None and lng is not None:
        set_clauses.append("location = ST_MakePoint(:lng, :lat)::geography")
        updates["lat"] = lat
        updates["lng"] = lng

    updates["id"] = store_id
    sql = text(f"""
        UPDATE stores SET {', '.join(set_clauses)}
        WHERE id = :id
        RETURNING
            id, name, address, city, state, active,
            ST_Y(location::geometry) AS latitude,
            ST_X(location::geometry) AS longitude
    """)
    row = db.execute(sql, updates).mappings().first()
    db.commit()
    return dict(row)


@router.delete("/admin/{store_id}")
def admin_deactivate_store(
    store_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Soft-delete: marks store as inactive."""
    db.execute(text("UPDATE stores SET active = false WHERE id = :id"), {"id": store_id})
    db.commit()
    return {"status": "deactivated", "id": store_id}
