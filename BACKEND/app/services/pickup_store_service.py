# # app/services/pickup_store_service.py
# from sqlalchemy.orm import Session
# from sqlalchemy import func, and_
# from geoalchemy2.shape import from_shape
# from geoalchemy2.functions import ST_Distance
# from shapely.geometry import Point

# from app.models.models import (
#     Store,
#     Cart,
#     CartItem,
#     StoreInventory,
# )


# def get_pickup_eligible_stores(
#     db: Session,
#     user_id,
#     session_id,
#     lat: float,
#     lng: float,
#     radius_km: int = 15,
# ):
#     # 1. Fetch cart
#     cart = (
#         db.query(Cart)
#         .filter(
#             Cart.user_id == user_id,
#             Cart.session_id == session_id,
#         )
#         .first()
#     )

#     if not cart:
#         return []

#     cart_items = (
#         db.query(CartItem)
#         .filter(CartItem.cart_id == cart.id)
#         .all()
#     )

#     if not cart_items:
#         return []

#     # 2. User location
#     user_point = from_shape(Point(lng, lat), srid=4326)

#     # 3. Candidate stores by distance
#     candidate_stores = (
#         db.query(
#             Store,
#             (ST_Distance(Store.location, user_point) / 1000).label("distance_km"),
#         )
#         .filter(Store.active.is_(True))
#         .filter(ST_Distance(Store.location, user_point) <= radius_km * 1000)
#         .order_by("distance_km")
#         .all()
#     )

#     eligible_stores = []

#     for store, distance in candidate_stores:
#         ok = True

#         for item in cart_items:
#             inv = (
#                 db.query(StoreInventory)
#                 .filter(
#                     StoreInventory.store_id == store.id,
#                     StoreInventory.product_variant_id == item.product_variant_id,
#                     StoreInventory.in_stock >= item.quantity,
#                 )
#                 .first()
#             )

#             if not inv:
#                 ok = False
#                 break

#         if ok:
#             eligible_stores.append({
#                 "store_id": store.id,
#                 "name": store.name,
#                 "city": store.city,
#                 "distance_km": round(distance, 2),
#                 "available_for_pickup": True,
#             })

#     return eligible_stores
