# app/api/routers/stores.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.deps import get_db
from app.schemas.schemas import StoreLookupRequest
from app.services.store_availability_service import get_nearest_stores_with_cart
from app.models.models import Store
from sqlalchemy import text

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.post("/nearest")
def nearest(data: StoreLookupRequest, db: Session = Depends(get_db)):
    return get_nearest_stores_with_cart(db, data.cart_id, data.latitude, data.longitude)


@router.get("/nearby")
def nearby_stores_mapbox(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius_km: float = Query(20.0, description="Search radius in kilometres"),
    db: Session = Depends(get_db),
):
    """
    Returns stores near (lat, lng) within radius_km, ordered by distance.
    Used by the Mapbox store picker in the frontend pickup checkout flow.
    Each store includes available_stock (sum across all variants in the area).
    """
    # PostGIS geography distance query
    sql = text("""
        SELECT
            s.id,
            s.name,
            s.address,
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
          AND ST_DWithin(
              s.location,
              ST_MakePoint(:lng, :lat)::geography,
              :radius_m
          )
        GROUP BY s.id, s.name, s.address, s.location
        ORDER BY distance_km ASC
        LIMIT 20
    """)

    rows = db.execute(sql, {
        "lat": lat,
        "lng": lng,
        "radius_m": radius_km * 1000,
    }).mappings().all()

    return [dict(r) for r in rows]
