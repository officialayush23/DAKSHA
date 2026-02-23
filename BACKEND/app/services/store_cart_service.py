# # app/services/store_cart_service.py
# from sqlalchemy.orm import Session
# from sqlalchemy import func

# from app.models.models import (
#     Store, StoreInventory, CartItem
# )


# def get_stores_for_cart(
#     db: Session,
#     *,
#     cart_id,
#     user_location_wkt,  # POINT(lon lat)
#     limit: int = 10,
# ):
#     items = (
#         db.query(CartItem)
#         .filter(CartItem.cart_id == cart_id)
#         .all()
#     )
#     if not items:
#         return []

#     variant_ids = [i.product_variant_id for i in items]

#     stores = db.query(
#         Store.id,
#         Store.name,
#         Store.city,
#         Store.state,
#         func.ST_Distance(
#             Store.location,
#             func.ST_GeomFromText(user_location_wkt, 4326),
#         ).label("distance"),
#     ).filter(Store.active.is_(True)).order_by("distance").limit(limit).all()

#     results = []

#     for s in stores:
#         stock_rows = (
#             db.query(StoreInventory)
#             .filter(
#                 StoreInventory.store_id == s.id,
#                 StoreInventory.product_variant_id.in_(variant_ids),
#             )
#             .all()
#         )

#         stock_map = {
#             r.product_variant_id: r.in_stock
#             for r in stock_rows
#         }

#         availability = []
#         for item in items:
#             available_qty = stock_map.get(item.product_variant_id, 0)
#             availability.append({
#                 "variant_id": item.product_variant_id,
#                 "requested_qty": item.quantity,
#                 "available_qty": available_qty,
#                 "can_fulfill": available_qty >= item.quantity,
#             })

#         results.append({
#             "store_id": s.id,
#             "name": s.name,
#             "city": s.city,
#             "state": s.state,
#             "distance_meters": float(s.distance),
#             "items": availability,
#         })

#     return results
