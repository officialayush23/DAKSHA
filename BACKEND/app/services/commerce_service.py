# app/services/commerce_service.py

from app.core.database import supabase_admin
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import List, Dict, Optional
import math


class CommerceService:
    """
    Authoritative commerce orchestration.
    All writes go through Postgres RPCs.
    """

    # --------------------------------------------------
    # CART
    # --------------------------------------------------

    @staticmethod
    def get_cart_snapshot(user_id: str):
        cart = (
            supabase_admin.table("carts")
            .select("id, status")
            .eq("user_id", user_id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        ).data

        if not cart:
            return None

        items = (
            supabase_admin.table("cart_items")
            .select("""
                id,
                quantity,
                product_variants (
                    id,
                    sku,
                    attributes,
                    products (
                        name,
                        base_price
                    )
                )
            """)
            .eq("cart_id", cart["id"])
            .execute()
        ).data or []

        total = 0
        for i in items:
            pv = i["product_variants"]
            price = pv["attributes"].get("price_override") or pv["products"]["base_price"]
            total += price * i["quantity"]

        return {
            "cart": cart,
            "items": items,
            "total": total
        }

    # --------------------------------------------------
    # INVENTORY RESERVATION
    # --------------------------------------------------

    @staticmethod
    def reserve_inventory(
        user_id: str,
        cart_id: UUID,
        variant_id: UUID,
        location_id: UUID,
        quantity: int,
    ):
        res = supabase_admin.rpc(
            "reserve_inventory",
            {
                "p_user_id": user_id,
                "p_cart_id": cart_id,
                "p_variant_id": variant_id,
                "p_location_id": location_id,
                "p_quantity": quantity,
            },
        ).execute()

        if hasattr(res, 'error') and res.error:
            raise HTTPException(500, res.error.message)

        return res.data

    # --------------------------------------------------
    # CHECKOUT
    # --------------------------------------------------

    @staticmethod
    def checkout_commit(
        user_id: str,
        order_type: str,
        pickup_location_id: str | None,
        address_id: str | None,
        promotion_code: str | None,
    ):
        cart = (
            supabase_admin.table("carts")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        ).data

        if not cart:
            raise HTTPException(400, "No active cart")

        # 1️⃣ Create Order
        order_id = supabase_admin.rpc(
            "create_order_from_cart",
            {
                "p_user_id": user_id,
                "p_cart_id": cart["id"],
                "p_order_type": order_type,
                "p_fulfillment_location_id": pickup_location_id,
                "p_address_id": address_id,
            },
        ).execute().data

        # 2️⃣ Commit inventory
        supabase_admin.rpc(
            "commit_inventory_for_order",
            {"p_order_id": order_id},
        ).execute()

        return {
            "order_id": order_id,
            "status": "pending_payment",
        }

    # --------------------------------------------------
    # PRICING (Read-only calculations)
    # --------------------------------------------------

    @staticmethod
    def calculate_pricing(items: list, promotion_code: str | None):
        """Calculate pricing with promotions"""
        # Calculate subtotal from items
        subtotal = 0
        for i in items:
            pv = i.get("product_variants", {})
            price = pv.get("attributes", {}).get("price_override") or pv.get("products", {}).get("base_price", 0)
            subtotal += price * i.get("quantity", 0)
        
        discount = 0.0
        promo_id = None

        if promotion_code:
            promo = (
                supabase_admin.table("promotions")
                .select("*")
                .eq("code", promotion_code)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            ).data

            if promo:
                promo_id = promo["id"]
                if promo["discount_type"] == "percentage":
                    discount = subtotal * (promo["discount_value"] / 100)
                elif promo["discount_type"] == "fixed_amount":
                    discount = promo["discount_value"]

                discount = min(discount, subtotal)

        tax = subtotal * 0.05
        total = subtotal - discount + tax

        return {
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "shipping": 0,
            "total": total,
            "promotion_id": promo_id,
        }

    # --------------------------------------------------
    # ALLOCATION (Read-only logic)
    # --------------------------------------------------

    @staticmethod
    def allocate_fulfillment(
        *,
        order_type: str,
        items: List[dict],
        pickup_location_id: Optional[str],
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
    ):
        """
        Allocation policy:
        1) Pickup -> user-selected store only
        2) Delivery: Warehouse-first, then nearest store fallback
        """
        required_qty = {
            i["product_variant_id"]: int(i["quantity"])
            for i in items
        }

        # PICKUP
        if order_type == "pickup":
            if not pickup_location_id:
                raise HTTPException(400, "pickup_location_id required")

            if not CommerceService._can_fulfill(pickup_location_id, required_qty):
                raise HTTPException(
                    400, "Pickup location cannot fulfill entire order"
                )

            return {
                "fulfillment_location_id": pickup_location_id,
                "allocation_type": "store",
                "reasoning": {
                    "policy": "pickup_only",
                    "explanation": "User-selected store can fulfill order",
                },
            }

        # DELIVERY: WAREHOUSE FIRST
        warehouses = CommerceService._get_locations("warehouse")
        for wh in warehouses:
            if CommerceService._can_fulfill(wh["id"], required_qty):
                return {
                    "fulfillment_location_id": wh["id"],
                    "allocation_type": "warehouse",
                    "reasoning": {
                        "policy": "warehouse_first",
                        "warehouse": wh,
                        "explanation": "Warehouse can fulfill entire order",
                    },
                }

        # DELIVERY: NEAREST STORE
        stores = CommerceService._get_locations("store")
        candidates = []

        for s in stores:
            if not CommerceService._can_fulfill(s["id"], required_qty):
                continue

            distance = CommerceService._distance(user_lat, user_lng, s)
            candidates.append({
                "store_id": s["id"],
                "name": s["name"],
                "distance_km": distance,
            })

        if not candidates:
            raise HTTPException(
                409, "Order cannot be fulfilled from a single location"
            )

        candidates.sort(key=lambda x: x["distance_km"])
        winner = candidates[0]

        return {
            "fulfillment_location_id": winner["store_id"],
            "allocation_type": "store",
            "reasoning": {
                "policy": "warehouse_fallback_store",
                "selected_store": winner,
                "alternatives": candidates[1:4],
                "explanation": "Nearest store selected",
            },
        }

    @staticmethod
    def _can_fulfill(location_id: str, required_qty: Dict[str, int]) -> bool:
        """Check if location can fulfill all required quantities"""
        rows = (
            supabase_admin.table("inventory")
            .select("product_variant_id, quantity_on_hand")
            .eq("fulfillment_location_id", location_id)
            .in_("product_variant_id", list(required_qty.keys()))
            .execute()
        ).data or []

        inv_map = {
            r["product_variant_id"]: r["quantity_on_hand"]
            for r in rows
        }

        return all(inv_map.get(v, 0) >= q for v, q in required_qty.items())

    @staticmethod
    def _get_locations(loc_type: str):
        """Get active fulfillment locations by type"""
        return (
            supabase_admin.table("fulfillment_locations")
            .select("id, name, latitude, longitude")
            .eq("type", loc_type)
            .eq("is_active", True)
            .execute()
        ).data or []

    @staticmethod
    def _distance(user_lat, user_lng, loc):
        """Calculate distance in km using Haversine formula"""
        if user_lat is None or user_lng is None:
            return float("inf")

        R = 6371
        phi1, phi2 = math.radians(user_lat), math.radians(loc["latitude"])
        dphi = math.radians(loc["latitude"] - user_lat)
        dl = math.radians(loc["longitude"] - user_lng)

        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
        )
        return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

    # --------------------------------------------------
    # CHECKOUT PREVIEW (Read-only)
    # --------------------------------------------------

    @staticmethod
    def checkout_preview(
        user_id: str,
        order_type: str,
        pickup_location_id,
        address_id,
        promotion_code,
    ):
        """Preview checkout with pricing and allocation"""
        snapshot = CommerceService.get_cart_snapshot(user_id)
        if not snapshot or not snapshot["items"]:
            raise HTTPException(400, "Cart is empty")

        pricing = CommerceService.calculate_pricing(
            snapshot["items"], promotion_code
        )

        # LOCATION RESOLUTION
        user_lat = user_lng = None
        if order_type == "delivery" and address_id:
            addr = (
                supabase_admin.table("user_addresses")
                .select("latitude, longitude")
                .eq("id", address_id)
                .maybe_single()
                .execute()
            ).data
            if addr:
                user_lat = float(addr["latitude"])
                user_lng = float(addr["longitude"])

        allocation_items = []
        for i in snapshot["items"]:
            pv = i.get("product_variants", {})
            allocation_items.append({
                "product_variant_id": pv.get("id"),
                "quantity": i.get("quantity", 0),
            })

        allocation = CommerceService.allocate_fulfillment(
            order_type=order_type,
            items=allocation_items,
            pickup_location_id=pickup_location_id,
            user_lat=user_lat,
            user_lng=user_lng,
        )

        return {
            "cart": snapshot["cart"],
            "items": snapshot["items"],
            "pricing": pricing,
            "fulfillment": allocation,
        }

    # Backward compatibility aliases
    get_cart = get_cart_snapshot
    checkout = checkout_commit
    
    # Legacy methods (kept for compatibility, but cart mutations should use RPCs)
    @staticmethod
    def get_or_create_cart(user_id: str):
        """Get active cart or create new one - NOTE: Should use RPC for cart mutations"""
        cart = (
            supabase_admin.table("carts")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        ).data

        if cart:
            return cart

        return (
            supabase_admin.table("carts")
            .insert({"user_id": user_id, "status": "active"})
            .select("*")
            .execute()
        ).data[0]

    @staticmethod
    def add_item(
        user_id: str,
        variant_id: str,
        qty: int,
        fulfillment_location_id: str,
    ):
        """Add item to cart - NOTE: Should use RPC for cart mutations"""
        if qty <= 0:
            raise HTTPException(400, "Quantity must be > 0")

        cart = CommerceService.get_or_create_cart(user_id)

        # Note: upsert() may need .select() in some cases, but insert() does not
        supabase_admin.table("cart_items").upsert(
            {
                "cart_id": cart["id"],
                "product_variant_id": variant_id,
                "quantity": qty,
            },
            on_conflict="cart_id,product_variant_id",
        ).execute()

        return {"cart_id": cart["id"]}

    @staticmethod
    def update_item_quantity(user_id: str, item_id: str, quantity: int):
        """
        Updates the quantity of a specific item in the user's active cart.
        """
        cart_snapshot = CommerceService.get_cart_snapshot(user_id)
        if not cart_snapshot or not cart_snapshot.get("cart"):
            raise HTTPException(status_code=404, detail="Active cart not found.")

        cart_id = cart_snapshot["cart"]["id"]

        # Check if the item exists in the cart and belongs to this cart
        existing_item = (
            supabase_admin.table("cart_items")
            .select("id")
            .eq("id", item_id)
            .eq("cart_id", cart_id)
            .maybe_single()
            .execute()
        ).data

        if not existing_item:
            raise HTTPException(status_code=404, detail="Cart item not found or does not belong to your cart.")

        if quantity <= 0:
            # If quantity is 0 or less, remove the item
            supabase_admin.table("cart_items").delete().eq("id", item_id).execute()
            return {"status": "removed", "item_id": item_id}
        else:
            # Otherwise, update the quantity
            res = (
                supabase_admin.table("cart_items")
                .update({"quantity": quantity})
                .eq("id", item_id)
                .execute()
            )
            if res.data:
                return {"status": "updated", "item_id": item_id, "new_quantity": quantity}
            else:
                raise HTTPException(status_code=500, detail="Failed to update cart item quantity.")
