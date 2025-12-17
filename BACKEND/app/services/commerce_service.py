# app/services/commerce_service.py
from fastapi import HTTPException
from app.database import supabase
from app.services.allocation_service import AllocationService
from app.services.human_handoff_service import HumanHandoffService
from typing import List, Optional
from datetime import datetime, timedelta

RESERVATION_TTL_MINUTES = 15
DEFAULT_FULFILLMENT_SLA_HOURS = 48


class CommerceService:
    # =========================================================
    # CART HELPERS
    # =========================================================

    @staticmethod
    def _get_cart(user_id: str):
        return (
            supabase.table("carts")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        ).data

    @staticmethod
    def _get_or_create_cart(user_id: str):
        cart = CommerceService._get_cart(user_id)
        if cart:
            return cart

        return (
            supabase.table("carts")
            .insert({"user_id": user_id, "status": "active"})
            .execute()
        ).data[0]

    # =========================================================
    # ADD TO CART (PURE)
    # =========================================================

    @staticmethod
    async def add_to_cart(user_id: str, variant_id: str, qty: int):
        if qty <= 0:
            raise HTTPException(400, "Quantity must be greater than zero")

        cart = CommerceService._get_or_create_cart(user_id)

        supabase.table("cart_items").upsert(
            {
                "cart_id": cart["id"],
                "product_variant_id": variant_id,
                "quantity": qty,
            },
            on_conflict="cart_id,product_variant_id",
        ).execute()

        return {"status": "success", "cart_id": cart["id"]}

    # =========================================================
    # CART SNAPSHOT
    # =========================================================

    @staticmethod
    def get_cart_snapshot(user_id: str):
        cart = CommerceService._get_cart(user_id)
        if not cart:
            return None

        rows = (
            supabase.table("cart_items")
            .select(
                "quantity, "
                "product_variants(id, price_override, image_url, color_name, size_label, "
                "products(id, name, base_price))"
            )
            .eq("cart_id", cart["id"])
            .execute()
        ).data or []

        items = []
        for row in rows:
            pv = row["product_variants"]
            p = pv["products"]

            unit_price = float(pv["price_override"] or p["base_price"])

            items.append({
                "product_id": p["id"],
                "product_name": p["name"],
                "variant_id": pv["id"],
                "variant_label": f'{pv.get("color_name","")} {pv.get("size_label","")}'.strip(),
                "image_url": pv.get("image_url"),
                "quantity": row["quantity"],
                "unit_price": unit_price,
                "line_total": unit_price * row["quantity"],
            })

        pricing = CommerceService._calculate_totals(items, None)

        return {
            "cart": cart,
            "items": items,
            "pricing": pricing,
            "fulfillment_preview": None,
        }

    # =========================================================
    # CHECKOUT PREVIEW (NO MUTATION)
    # =========================================================

    @staticmethod
    def checkout_preview(
        user_id: str,
        order_type: str,
        pickup_location_id: Optional[str],
        address_id: Optional[str],
        promotion_code: Optional[str],
    ):
        snapshot = CommerceService.get_cart_snapshot(user_id)
        if not snapshot or not snapshot["items"]:
            raise HTTPException(400, "Cart is empty")

        items = snapshot["items"]

        pricing = CommerceService._calculate_totals(items, promotion_code)

        allocation_items = [
            {"product_variant_id": i["variant_id"], "quantity": i["quantity"]}
            for i in items
        ]

        user_lat = user_lng = None
        if order_type == "delivery":
            addr = (
                supabase.table("user_addresses")
                .select("latitude, longitude")
                .eq("id", address_id)
                .single()
                .execute()
            ).data
            user_lat = float(addr["latitude"])
            user_lng = float(addr["longitude"])

        allocation = AllocationService.allocate(
            order_type=order_type,
            items=allocation_items,
            pickup_location_id=pickup_location_id,
            user_lat=user_lat,
            user_lng=user_lng,
        )

        return {
            "pricing": pricing,
            "allocation": allocation,
        }

    # =========================================================
    # CHECKOUT (AUTHORITATIVE)
    # =========================================================

    @staticmethod
    def checkout(
        user_id: str,
        order_type: str,
        pickup_location_id: Optional[str],
        address_id: Optional[str],
        promotion_code: Optional[str],
    ):
        snapshot = CommerceService.get_cart_snapshot(user_id)
        if not snapshot or not snapshot["items"]:
            raise HTTPException(400, "Cart is empty")

        cart = snapshot["cart"]
        items = snapshot["items"]

        # 🔒 IDEMPOTENCY
        existing = (
            supabase.table("orders")
            .select("*")
            .eq("cart_id", cart["id"])
            .maybe_single()
            .execute()
        ).data

        if existing:
            return {"order": existing, "idempotent": True}

        preview = CommerceService.checkout_preview(
            user_id,
            order_type,
            pickup_location_id,
            address_id,
            promotion_code,
        )

        pricing = preview["pricing"]
        allocation = preview["allocation"]
        fulfillment_location_id = allocation["fulfillment_location_id"]

        # ---- INVENTORY RESERVATION ----
        for item in items:
            supabase.table("inventory_reservations").insert({
                "cart_id": cart["id"],
                "product_variant_id": item["variant_id"],
                "fulfillment_location_id": fulfillment_location_id,
                "quantity": item["quantity"],
                "status": "active",
                "expires_at": datetime.utcnow()
                + timedelta(minutes=RESERVATION_TTL_MINUTES),
            }).execute()

        order = (
            supabase.table("orders")
            .insert({
                "cart_id": cart["id"],
                "user_id": user_id,
                "status": "pending",
                "type": order_type,
                "total_amount": pricing["total"],
                "discount_amount": pricing["discount"],
                "delivery_address_id": address_id,
                "applied_promotion_id": pricing["promotion_id"],
            })
            .execute()
        ).data[0]

        supabase.table("order_items").insert(
            [
                {
                    "order_id": order["id"],
                    "product_variant_id": i["variant_id"],
                    "quantity": i["quantity"],
                    "price_at_purchase": i["unit_price"],
                    "fulfillment_location_id": fulfillment_location_id,
                }
                for i in items
            ]
        ).execute()

        supabase.table("fulfillments").insert({
            "order_id": order["id"],
            "fulfillment_location_id": fulfillment_location_id,
            "status": "pending",
            "type": order_type,
            "sla_deadline": datetime.utcnow()
            + timedelta(hours=DEFAULT_FULFILLMENT_SLA_HOURS),
        }).execute()

        supabase.table("inventory_reservations") \
            .update({"status": "consumed"}) \
            .eq("cart_id", cart["id"]) \
            .eq("status", "active") \
            .execute()

        supabase.table("carts") \
            .update({"status": "converted"}) \
            .eq("id", cart["id"]) \
            .execute()

        return {"order": order, "allocation": allocation}

    # =========================================================
    # PRICING
    # =========================================================

    @staticmethod
    def _calculate_totals(items: List[dict], promotion_code: Optional[str]):
        subtotal = sum(i["unit_price"] * i["quantity"] for i in items)

        discount = 0.0
        promo_id = None

        if promotion_code:
            promo = (
                supabase.table("promotions")
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

        tax = round(subtotal * 0.05, 2)
        shipping = 0 if subtotal > 1000 else 50

        return {
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "shipping": shipping,
            "total": subtotal - discount + tax + shipping,
            "promotion_id": promo_id,
        }
