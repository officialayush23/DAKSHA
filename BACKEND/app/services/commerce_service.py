from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus
from app.services.store_service import StoreService
from typing import List, Dict, Optional, Tuple
import math
from app.services.allocation_service import AllocationService
from datetime import timedelta, datetime


RESERVATION_TTL_MINUTES = 15
class CommerceService:

    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------

    @staticmethod
    def _get_cart(user_id: str) -> Optional[dict]:
        cart = (
            supabase.table("carts")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        ).data
        return cart

    @staticmethod
    def _get_or_create_cart(user_id: str) -> dict:
        cart = CommerceService._get_cart(user_id)
        if cart:
            return cart

        res = (
            supabase.table("carts")
            .insert({"user_id": user_id, "status": "active"})
            .execute()
        ).data[0]
        return res

    # ------------------------------------------------------------------
    # ADD TO CART  (Delivery cart does NOT need store_id anymore)
    # ------------------------------------------------------------------

    @staticmethod
    async def add_to_cart(user_id: str, variant_id: str, store_location_id: str, qty: int):
        """
        store_location_id is only used when the frontend explicitly adds from a store page.
        For delivery orders, frontend will pass the warehouse location_id.
        """

        # Lock inventory row at that location
        inv = (
            supabase.table("inventory")
            .select(
                "id, fulfillment_location_id, product_variant_id, "
                "quantity_on_hand, quantity_reserved, version"
            )
            .eq("product_variant_id", variant_id)
            .eq("fulfillment_location_id", store_location_id)
            .single()
            .execute()
        ).data

        if not inv or inv["quantity_on_hand"] < qty:
            raise HTTPException(400, "Insufficient stock at this location")

        # Optimistic version-check update
        updated = (
            supabase.table("inventory")
            .update({
                "quantity_on_hand": inv["quantity_on_hand"] - qty,
                "quantity_reserved": inv["quantity_reserved"] + qty,
                "version": inv["version"] + 1
            })
            .eq("id", inv["id"])
            .eq("version", inv["version"])
            .execute()
        ).data

        if not updated:
            raise HTTPException(409, "Stock changed concurrently. Retry")
        

        supabase.table("inventory_reservations").insert(
        {
            "cart_id": cart["id"],
            "product_variant_id": variant_id,
            "fulfillment_location_id": fulfillment_location_id,
            "quantity": qty,
            "status": "active",
            "expires_at": datetime.utcnow() + timedelta(minutes=RESERVATION_TTL_MINUTES),
        }
        ).execute()


        # Realtime push update
        await EventBus.notify_store_inventory(
            str(store_location_id),
            {
                "inventory_id": inv["id"],
                "product_variant_id": inv["product_variant_id"],
                "quantity_on_hand": updated[0]["quantity_on_hand"],
                "quantity_reserved": updated[0]["quantity_reserved"],
            },
        )

        # Insert into cart
        cart = CommerceService._get_or_create_cart(user_id)

        supabase.table("cart_items").upsert(
            {
                "cart_id": cart["id"],
                "product_variant_id": variant_id,
                "quantity": qty,
                "store_id": None,  # deprecated for delivery; preserved for backward compatibility
            },
            on_conflict="cart_id,product_variant_id"
        ).execute()

        return {"status": "success", "cart_id": cart["id"]}

    # ------------------------------------------------------------------
    # CART LISTING
    # ------------------------------------------------------------------

    @staticmethod
    def get_cart_with_items(user_id: str):
        cart = CommerceService._get_cart(user_id)
        if not cart:
            return None

        items = (
            supabase.table("cart_items")
            .select(
                "id, quantity, "
                "product_variants(id, sku, price_override, product_id, "
                "products(name, base_price))"
            )
            .eq("cart_id", cart["id"])
            .execute()
        ).data

        return {"cart": cart, "items": items}

    # ------------------------------------------------------------------
    # CHECKOUT ENGINE — Warehouse-first + nearest store fallback
    # ------------------------------------------------------------------

    @staticmethod
    def checkout(
        user_id: str,
        order_type: str,
        store_pickup_location_id: Optional[str],
        address_id: Optional[str],
        promotion_code: Optional[str],
    ):
        """
        Master checkout:
        - Delivery: warehouse → fallback to single store
        - Pickup: explicit store only
        - No split unless absolutely unavoidable
        - Stores allocation reasoning for agent
        """

        # --------------------------------------------------
        # 1) Load cart
        # --------------------------------------------------
        cart_data = CommerceService.get_cart_with_items(user_id)
        if not cart_data or not cart_data["items"]:
            raise HTTPException(400, "Cart is empty")

        cart = cart_data["cart"]
        items = cart_data["items"]

        # --------------------------------------------------
        # 2) Calculate totals
        # --------------------------------------------------
        total, discount, applied_promo_id = CommerceService._calculate_totals(
            items, promotion_code
        )

        # --------------------------------------------------
        # 3) Prepare lightweight item payload for allocation
        # --------------------------------------------------
        allocation_items = [
            {
                "product_variant_id": row["product_variants"]["id"],
                "quantity": int(row["quantity"]),
            }
            for row in items
        ]

        # --------------------------------------------------
        # 4) Fulfillment allocation (CORE LOGIC)
        # --------------------------------------------------
        allocation = AllocationService.allocate(
            order_type=order_type,
            items=allocation_items,
            pickup_location_id=store_pickup_location_id,
        )

        fulfillment_location_id = allocation["fulfillment_location_id"]

        # --------------------------------------------------
        # 5) Create ORDER
        # --------------------------------------------------
        order_payload = {
            "user_id": user_id,
            "status": "pending",
            "type": order_type,
            "total_amount": total,
            "discount_amount": discount,
            "delivery_address_id": address_id,
            "applied_promotion_id": applied_promo_id,
        }

        order = (
            supabase.table("orders")
            .insert(order_payload)
            .execute()
        ).data[0]

        # --------------------------------------------------
        # 6) Create ORDER ITEMS + reserve inventory
        # --------------------------------------------------
        order_items_payload = []

        for row in items:
            pv = row["product_variants"]
            base_price = float(pv["products"]["base_price"])
            price = float(pv["price_override"] or base_price)

            order_items_payload.append(
                {
                    "order_id": order["id"],
                    "product_variant_id": pv["id"],
                    "quantity": int(row["quantity"]),
                    "price_at_purchase": price,
                    "fulfillment_location_id": fulfillment_location_id,
                }
            )

        supabase.table("order_items").insert(order_items_payload).execute()

        supabase.table("inventory_reservations").update(
        {"status": "consumed"}
        ).eq("cart_id", cart["id"]).eq("status", "active").execute()


        # --------------------------------------------------
        # 7) Persist allocation reasoning (agent-safe)
        # --------------------------------------------------
        supabase.table("order_allocations").insert(
            {
                "order_id": order["id"],
                "fulfillment_location_id": fulfillment_location_id,
                "allocation_type": allocation["allocation_type"],
                "reasoning": allocation["reasoning"],
            }
        ).execute()

        # --------------------------------------------------
        # 8) Convert cart
        # --------------------------------------------------
        supabase.table("carts") \
            .update({"status": "converted"}) \
            .eq("id", cart["id"]) \
            .execute()

        # --------------------------------------------------
        # 9) Return enriched response
        # --------------------------------------------------
        return {
            "order": order,
            "allocation": allocation,
        }

    # ------------------------------------------------------------------
    # PRICE + PROMO
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_totals(items: List[dict], promo_code: Optional[str]):
        total = 0.0
        for row in items:
            pv = row["product_variants"]
            base_price = float(pv["products"]["base_price"])
            price = float(pv["price_override"] or base_price)
            total += price * row["quantity"]

        discount = 0.0
        if promo_code:
            promo = (
                supabase.table("promotions")
                .select("*")
                .eq("code", promo_code)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            ).data

            if promo:
                if promo["discount_type"] == "percentage":
                    discount = total * float(promo["discount_value"]) / 100
                elif promo["discount_type"] == "fixed_amount":
                    discount = float(promo["discount_value"])
                discount = min(discount, total)

        return total, discount

    # ------------------------------------------------------------------
    # ALLOCATION LOGIC — DELIVERY
    # ------------------------------------------------------------------

    @staticmethod
    def _allocate_delivery(user_id: str, items, address_id):
        """
        Steps:
        1) Try warehouse single-source → MUST satisfy all items
        2) If fails → find nearest stores to user
        3) Try store single-source
        4) If fails → return failure + reasoning
        """
        # -------- LOAD ALL warehouses --------
        warehouses = (
            supabase.table("fulfillment_locations")
            .select("id, latitude, longitude, type")
            .eq("type", "warehouse")
            .eq("is_active", True)
            .execute()
        ).data

        # -------- Step 1: warehouse-first --------
        for wh in warehouses:
            ok, missing = CommerceService._location_has_all_items(wh["id"], items)
            if ok:
                return (
                    {row["product_variants"]["id"]: wh["id"] for row in items},
                    f"Allocated from warehouse {wh['id']} because it had full stock."
                )

        # -------- Step 2: nearest active stores --------
        if address_id:
            user_address = (
                supabase.table("user_addresses")
                .select("latitude, longitude")
                .eq("id", address_id)
                .single()
                .execute()
            ).data
            if not user_address or not user_address["latitude"]:
                return None, "Delivery address missing coordinates."

            nearest = StoreService.find_nearest_stores(
                lat=float(user_address["latitude"]),
                lng=float(user_address["longitude"]),
                limit=5
            )
        else:
            nearest = StoreService.find_nearest_stores(0, 0, limit=5)

        # -------- Step 3: try each store --------
        for st in nearest:
            location_id = st["fulfillment_location_id"]
            ok, missing = CommerceService._location_has_all_items(location_id, items)
            if ok:
                return (
                    {row["product_variants"]["id"]: location_id for row in items},
                    f"Allocated from store {st['id']} (nearest with all items available)."
                )

        # -------- Step 4: Fail (no-split policy) --------
        return None, "No single warehouse or store had 100% of the cart. We avoid splitting orders unless the user explicitly chooses pickup."

    # ------------------------------------------------------------------
    # ALLOCATION LOGIC — PICKUP
    # ------------------------------------------------------------------

    @staticmethod
    def _allocate_pickup(items, store_location_id):
        ok, missing = CommerceService._location_has_all_items(store_location_id, items)
        if ok:
            return (
                {row["product_variants"]["id"]: store_location_id for row in items},
                "Allocated for pickup at chosen store; all items available."
            )
        return None, f"Pickup store is missing variants: {missing}"

    # ------------------------------------------------------------------
    # CHECK IF LOCATION CAN FULFILL ALL ITEMS
    # ------------------------------------------------------------------

    @staticmethod
    def _location_has_all_items(location_id: str, items: List[dict]) -> Tuple[bool, List[str]]:
        missing = []
        for row in items:
            variant = row["product_variants"]
            qty_req = row["quantity"]

            inv = (
                supabase.table("inventory")
                .select("quantity_on_hand")
                .eq("product_variant_id", variant["id"])
                .eq("fulfillment_location_id", location_id)
                .maybe_single()
                .execute()
            ).data

            if not inv or inv["quantity_on_hand"] < qty_req:
                missing.append(variant["id"])

        return (len(missing) == 0), missing

    # ------------------------------------------------------------------
    # APPLY STOCK CHANGES + CREATE ORDER ITEMS + FULFILLMENT SOURCE RECORD
    # ------------------------------------------------------------------

    @staticmethod
    def _finalize_allocation(order_id: str, items, allocation: Dict[str, str]):
        """
        Deduct reserved → final stock.
        Create order_items + fulfillment_sources entries.
        """
        fulfillment_rows = []

        for row in items:
            pv = row["product_variants"]
            variant_id = pv["id"]
            qty = row["quantity"]
            location_id = allocation[variant_id]

            # Fetch inventory row
            inv = (
                supabase.table("inventory")
                .select("id, quantity_on_hand, quantity_reserved, version")
                .eq("product_variant_id", variant_id)
                .eq("fulfillment_location_id", location_id)
                .single()
                .execute()
            ).data

            if not inv or inv["quantity_reserved"] < qty:
                raise HTTPException(500, "Stock inconsistency: reserved < required")

            updated = (
                supabase.table("inventory")
                .update({
                    "quantity_reserved": inv["quantity_reserved"] - qty,
                    "version": inv["version"] + 1
                })
                .eq("id", inv["id"])
                .eq("version", inv["version"])
                .execute()
            ).data

            if not updated:
                raise HTTPException(409, "Concurrent stock change during checkout")

            # Create order item
            base_price = float(pv["products"]["base_price"])
            price = float(pv["price_override"] or base_price)

            (
                supabase.table("order_items")
                .insert({
                    "order_id": order_id,
                    "product_variant_id": variant_id,
                    "quantity": qty,
                    "price_at_purchase": price,
                    "fulfillment_location_id": location_id
                })
                .execute()
            )

            fulfillment_rows.append({
                "order_id": order_id,
                "source_type": "store" if CommerceService._is_store(location_id) else "warehouse",
                "source_id": location_id,
            })

        # Insert fulfillment source rows
        if fulfillment_rows:
            supabase.table("fulfillment_sources").insert(fulfillment_rows).execute()

    @staticmethod
    def _is_store(location_id: str) -> bool:
        st = (
            supabase.table("stores")
            .select("id")
            .eq("fulfillment_location_id", location_id)
            .maybe_single()
            .execute()
        ).data
        return bool(st)

    # ------------------------------------------------------------------
    # TRACKING
    # ------------------------------------------------------------------

    @staticmethod
    def track_order(order_id: str):
        order = (
            supabase.table("orders")
            .select("*")
            .eq("id", order_id)
            .maybe_single()
            .execute()
        ).data

        if not order:
            raise HTTPException(404, "Order not found")

        fulfillment = (
            supabase.table("fulfillments")
            .select("*")
            .eq("order_id", order_id)
            .order("shipped_at", desc=True)
            .maybe_single()
            .execute()
        ).data

        return {
            "order_id": order_id,
            "status": order["status"],
            "type": order["type"],
            "total_amount": order["total_amount"],
            "discount_amount": order["discount_amount"],
            "latest_fulfillment": fulfillment,
        }
