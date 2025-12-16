# app/services/commerce_service.py

from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus
from app.services.allocation_service import AllocationService
from app.services.human_handoff_service import HumanHandoffService
from typing import List, Optional
from datetime import timedelta, datetime

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
    # ADD TO CART (OPTIMISTIC + REALTIME)
    # =========================================================
    @staticmethod
    async def add_to_cart(
        user_id: str,
        variant_id: str,
        fulfillment_location_id: str,
        qty: int,
    ):
        inv = (
            supabase.table("inventory")
            .select(
                "id, quantity_on_hand, quantity_reserved, version"
            )
            .eq("product_variant_id", variant_id)
            .eq("fulfillment_location_id", fulfillment_location_id)
            .single()
            .execute()
        ).data

        if not inv or inv["quantity_on_hand"] < qty:
            raise HTTPException(400, "Insufficient stock")

        updated = (
            supabase.table("inventory")
            .update(
                {
                    "quantity_on_hand": inv["quantity_on_hand"] - qty,
                    "quantity_reserved": inv["quantity_reserved"] + qty,
                    "version": inv["version"] + 1,
                }
            )
            .eq("id", inv["id"])
            .eq("version", inv["version"])
            .execute()
        ).data

        if not updated:
            HumanHandoffService.trigger(
                session_id=None,
                user_id=user_id,
                reason="inventory_conflict",
                summary="Concurrent inventory update during add-to-cart",
            )
            raise HTTPException(409, "Inventory conflict")

        cart = CommerceService._get_or_create_cart(user_id)

        supabase.table("inventory_reservations").insert(
            {
                "cart_id": cart["id"],
                "product_variant_id": variant_id,
                "fulfillment_location_id": fulfillment_location_id,
                "quantity": qty,
                "status": "active",
                "expires_at": datetime.utcnow()
                + timedelta(minutes=RESERVATION_TTL_MINUTES),
            }
        ).execute()

        await EventBus.notify_inventory_update(
            fulfillment_location_id,
            {
                "product_variant_id": variant_id,
                "quantity_on_hand": updated[0]["quantity_on_hand"],
                "quantity_reserved": updated[0]["quantity_reserved"],
            },
        )

        supabase.table("cart_items").upsert(
            {
                "cart_id": cart["id"],
                "product_variant_id": variant_id,
                "quantity": qty,
                "fulfillment_location_id": fulfillment_location_id,
            },
            on_conflict="cart_id,product_variant_id",
        ).execute()

        return {"status": "success", "cart_id": cart["id"]}

    # =========================================================
    # CART READ (PURE, SAFE)
    # =========================================================
    @staticmethod
    def get_cart_snapshot(user_id: str):
        cart = CommerceService._get_cart(user_id)
        if not cart:
            return None

        rows = (
            supabase.table("cart_items")
            .select(
                "quantity, fulfillment_location_id, "
                "product_variants(id, price_override, image_url, color_name, size_label, "
                "products(id, name, base_price))"
            )
            .eq("cart_id", cart["id"])
            .execute()
        ).data or []

        items = []
        subtotal = 0.0

        for row in rows:
            pv = row["product_variants"]
            p = pv["products"]

            unit_price = float(pv["price_override"] or p["base_price"])
            line_total = unit_price * row["quantity"]
            subtotal += line_total

            items.append({
                "product_id": p["id"],
                "product_name": p["name"],
                "variant_id": pv["id"],
                "variant_label": f'{pv.get("color_name","")} {pv.get("size_label","")}'.strip(),
                "image_url": pv.get("image_url"),
                "quantity": row["quantity"],
                "unit_price": unit_price,
                "line_total": line_total,
                "inventory": {
                    "assumed_available": True,
                    "validated_at_checkout": True,
                }
            })

        tax = round(subtotal * 0.05, 2)
        shipping = 0 if subtotal > 1000 else 50

        return {
            "cart": cart,
            "items": items,
            "pricing": {
                "subtotal": subtotal,
                "discount": 0,
                "tax": tax,
                "shipping": shipping,
                "total": subtotal + tax + shipping,
                "applied_promotion": None,
            },
            "fulfillment_preview": {
                "deliverable": True,
                "type": "delivery",
            },
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
        

        cart_data = CommerceService.get_cart_with_items(user_id)
        if not cart_data or not cart_data["items"]:
            raise HTTPException(400, "Cart is empty")

        cart = cart_data["cart"]
        items = cart_data["items"]

        total, discount, promo_id = CommerceService._calculate_totals(
            items, promotion_code
        )

        allocation_items = [
            {
                "product_variant_id": row["product_variants"]["id"],
                "quantity": row["quantity"],
            }
            for row in items
        ]

        delivery_lat = delivery_lng = None
        if order_type == "delivery":
            addr = (
                supabase.table("user_addresses")
                .select("latitude, longitude")
                .eq("id", address_id)
                .single()
                .execute()
            ).data
            delivery_lat = float(addr["latitude"])
            delivery_lng = float(addr["longitude"])

        try:
            allocation = AllocationService.allocate(
                order_type=order_type,
                items=allocation_items,
                pickup_location_id=pickup_location_id,
                user_lat=delivery_lat,
                user_lng=delivery_lng,
            )
        except Exception as e:
            HumanHandoffService.trigger(
                session_id=None,
                user_id=user_id,
                reason="allocation_failure",
                summary=str(e),
            )
            raise

        fulfillment_location_id = allocation["fulfillment_location_id"]

        order = (
            supabase.table("orders")
            .insert(
                {
                    "user_id": user_id,
                    "status": "pending",
                    "type": order_type,
                    "total_amount": total,
                    "discount_amount": discount,
                    "delivery_address_id": address_id,
                    "applied_promotion_id": promo_id,
                }
            )
            .execute()
        ).data[0]

        supabase.table("order_items").insert(
            [
                {
                    "order_id": order["id"],
                    "product_variant_id": row["product_variants"]["id"],
                    "quantity": row["quantity"],
                    "price_at_purchase": float(
                        row["product_variants"]["price_override"]
                        or row["product_variants"]["products"]["base_price"]
                    ),
                    "fulfillment_location_id": fulfillment_location_id,
                }
                for row in items
            ]
        ).execute()

        supabase.table("inventory_reservations").update(
            {"status": "consumed"}
        ).eq("cart_id", cart["id"]) \
         .eq("fulfillment_location_id", fulfillment_location_id) \
         .eq("status", "active") \
         .execute()

        # 🔥 FULFILLMENT CREATION (CRITICAL)
        supabase.table("fulfillments").insert(
            {
                "order_id": order["id"],
                "fulfillment_location_id": fulfillment_location_id,
                "status": "pending",
                "type": order_type,
                "sla_deadline": datetime.utcnow()
                + timedelta(hours=DEFAULT_FULFILLMENT_SLA_HOURS),
            }
        ).execute()

        supabase.table("order_allocations").insert(
            {
                "order_id": order["id"],
                "fulfillment_location_id": fulfillment_location_id,
                "allocation_type": allocation["allocation_type"],
                "reasoning": allocation["reasoning"],
            }
        ).execute()

        supabase.table("carts") \
            .update({"status": "converted"}) \
            .eq("id", cart["id"]) \
            .execute()

        return {"order": order, "allocation": allocation}

    # =========================================================
    # PRICING
    # =========================================================
    @staticmethod
    def _calculate_totals(items: List[dict], promo_code: Optional[str]):
        total = sum(
            (
                float(row["product_variants"]["price_override"]
                or row["product_variants"]["products"]["base_price"])
                * row["quantity"]
            )
            for row in items
        )

        discount = 0.0
        promo_id = None

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
                promo_id = promo["id"]
                if promo["discount_type"] == "percentage":
                    discount = total * promo["discount_value"] / 100
                elif promo["discount_type"] == "fixed_amount":
                    discount = promo["discount_value"]
                discount = min(discount, total)

        return total, discount, promo_id

    # =========================================================
    # TRACKING
    # =========================================================
    @staticmethod
    def track_order(order_id: str):
        order = (
            supabase.table("orders")
            .select("*")
            .eq("id", order_id)
            .single()
            .execute()
        ).data

        fulfillment = (
            supabase.table("fulfillments")
            .select("*")
            .eq("order_id", order_id)
            .maybe_single()
            .execute()
        ).data

        return {
            "order": order,
            "fulfillment": fulfillment,
        }



    @staticmethod
    def get_cart_snapshot(user_id: str):
        cart_data = CommerceService.get_cart_with_items(user_id)
        if not cart_data:
            return None

        cart = cart_data["cart"]
        items_raw = cart_data["items"]

        items = []
        subtotal = 0.0

        for row in items_raw:
            pv = row["product_variants"]
            p = pv["products"]

            unit_price = float(pv["price_override"] or p["base_price"])
            line_total = unit_price * row["quantity"]
            subtotal += line_total

            items.append({
                "product_id": p["id"],
                "product_name": p["name"],
                "variant_id": pv["id"],
                "variant_label": f'{pv.get("color_name","")} {pv.get("size_label","")}'.strip(),
                "image_url": pv.get("image_url"),
                "quantity": row["quantity"],
                "unit_price": unit_price,
                "line_total": line_total,
                "inventory": {
                    "available": True,  # authoritative check happens at checkout
                    "available_qty": None
                }
            })

        tax = round(subtotal * 0.05, 2)
        shipping = 0 if subtotal > 1000 else 50
        total = subtotal + tax + shipping

        # Fulfillment preview (SAFE — no reservation)
        try:
            allocation = AllocationService.allocate(
                order_type="delivery",
                items=[
                    {"product_variant_id": i["variant_id"], "quantity": i["quantity"]}
                    for i in items
                ],
                pickup_location_id=None,
            )
        except Exception:
            allocation = None

        return {
            "cart": cart,
            "items": items,
            "pricing": {
                "subtotal": subtotal,
                "discount": 0,
                "tax": tax,
                "shipping": shipping,
                "total": total,
                "applied_promotion": None,
            },
            "fulfillment_preview": allocation,
        }



@staticmethod
def checkout_preview(
    user_id: str,
    order_type: str,
    pickup_location_id: Optional[str],
    address_id: Optional[str],
    promotion_code: Optional[str],
):
    cart_data = CommerceService.get_cart_with_items(user_id)
    if not cart_data or not cart_data["items"]:
        raise HTTPException(400, "Cart is empty")

    items = cart_data["items"]

    total, discount, promo_id = CommerceService._calculate_totals(
        items, promotion_code
    )

    allocation_items = [
        {
            "product_variant_id": row["product_variants"]["id"],
            "quantity": row["quantity"],
        }
        for row in items
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
        "pricing": {
            "subtotal": total,
            "discount": discount,
            "total": total - discount,
            "promotion_id": promo_id,
        },
        "allocation": allocation,
    }
