# app/service/store_availability_service.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID


def get_nearest_stores_with_cart(
    db: Session,
    cart_id: UUID,
    user_lat: float,
    user_lng: float,
    limit: int = 5,
):
    """
    Returns nearest stores with ALL cart items available.
    Uses PostGIS index-friendly search.
    """

    query = text("""
    WITH user_point AS (
        SELECT ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography AS pt
    ),
    cart_variants AS (
        SELECT product_variant_id, quantity
        FROM cart_items
        WHERE cart_id = :cart_id
    ),
    valid_stores AS (
        SELECT si.store_id
        FROM store_inventory si
        JOIN cart_variants cv
          ON si.product_variant_id = cv.product_variant_id
        WHERE si.in_stock >= cv.quantity
        GROUP BY si.store_id
        HAVING COUNT(*) = (SELECT COUNT(*) FROM cart_variants)
    )
    SELECT
        s.id,
        s.name,
        s.address,
        ST_Distance(s.location, up.pt) AS distance
    FROM stores s
    JOIN valid_stores vs ON vs.store_id = s.id
    CROSS JOIN user_point up
    WHERE ST_DWithin(s.location, up.pt, 20000) -- 20km search radius
    ORDER BY distance
    LIMIT :limit
    """)

    return db.execute(query, {
        "cart_id": cart_id,
        "lat": user_lat,
        "lng": user_lng,
        "limit": limit
    }).fetchall()