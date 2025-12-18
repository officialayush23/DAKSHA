from fastapi import HTTPException
from app.database import supabase
from app.services.allocation_service import AllocationService
from typing import List, Optional
from datetime import datetime, timedelta

RESERVATION_TTL_MINUTES = 15

class CommerceService:
    @staticmethod
    def _get_cart(user_id: str):
        return (supabase.table("carts").select("id").eq("user_id", user_id).eq("status", "active").maybe_single().execute()).data

    @staticmethod
    def _get_or_create_cart(user_id: str):
        cart = CommerceService._get_cart(user_id)
        if cart: return cart
        return (supabase.table("carts").insert({"user_id": user_id, "status": "active"}).execute()).data[0]

    @staticmethod
    async def add_to_cart(user_id: str, variant_id: str, qty: int, fulfillment_location_id: str = None):
        if qty <= 0: raise HTTPException(400, "Quantity must be > 0")
        cart = CommerceService._get_or_create_cart(user_id)
        supabase.table("cart_items").upsert({
            "cart_id": cart["id"], "product_variant_id": variant_id, "quantity": qty, "fulfillment_location_id": fulfillment_location_id
        }, on_conflict="cart_id,product_variant_id").execute()
        return {"status": "success", "cart_id": cart["id"]}

    @staticmethod
    def get_cart_snapshot(user_id: str):
        cart = CommerceService._get_cart(user_id)
        if not cart: return None
        rows = supabase.table("cart_items").select("quantity, product_variants(id, price_override, image_url, color_name, size_label, products(id, name, base_price))").eq("cart_id", cart["id"]).execute().data or []
        items = []
        for row in rows:
            pv = row["product_variants"]
            p = pv["products"]
            unit_price = float(pv["price_override"] or p["base_price"])
            items.append({
                "product_id": p["id"], "product_name": p["name"], "variant_id": pv["id"],
                "variant_label": f'{pv.get("color_name","")} {pv.get("size_label","")}'.strip(),
                "image_url": pv.get("image_url"), "quantity": row["quantity"],
                "unit_price": unit_price, "line_total": unit_price * row["quantity"]
            })
        pricing = CommerceService._calculate_totals(items, None)
        return {"cart": cart, "items": items, "pricing": pricing}

    @staticmethod
    def checkout_preview(user_id: str, order_type: str, pickup_location_id: Optional[str], address_id: Optional[str], promotion_code: Optional[str]):
        snapshot = CommerceService.get_cart_snapshot(user_id)
        if not snapshot or not snapshot["items"]: raise HTTPException(400, "Cart is empty")
        items = snapshot["items"]
        pricing = CommerceService._calculate_totals(items, promotion_code)
        
        user_lat = user_lng = None
        if order_type == "delivery" and address_id:
            addr = supabase.table("user_addresses").select("latitude, longitude").eq("id", address_id).maybe_single().execute().data
            if addr:
                user_lat, user_lng = float(addr.get("latitude") or 0), float(addr.get("longitude") or 0)

        allocation_items = [{"product_variant_id": i["variant_id"], "quantity": i["quantity"]} for i in items]
        
        allocation = AllocationService.allocate(
            order_type=order_type, items=allocation_items, pickup_location_id=pickup_location_id, user_lat=user_lat, user_lng=user_lng
        )
        return {"pricing": pricing, "allocation": allocation}

    @staticmethod
    def checkout(user_id: str, order_type: str, pickup_location_id: Optional[str], address_id: Optional[str], promotion_code: Optional[str]):
        snapshot = CommerceService.get_cart_snapshot(user_id)
        if not snapshot or not snapshot["items"]: raise HTTPException(400, "Cart is empty")
        cart = snapshot["cart"]
        items = snapshot["items"]

        # Idempotency
        existing = supabase.table("orders").select("*").eq("cart_id", cart["id"]).maybe_single().execute().data
        if existing: return {"order": existing, "idempotent": True}

        # Allocation
        preview = CommerceService.checkout_preview(user_id, order_type, pickup_location_id, address_id, promotion_code)
        pricing = preview["pricing"]
        allocation = preview["allocation"]
        fulfillment_location_id = allocation["fulfillment_location_id"]

        # --- CRITICAL FIX START ---
        # Resolve 'store_id' from 'fulfillment_location_id'
        # If allocated to a Warehouse, store_id MUST be None.
        resolved_store_id = None
        store_check = supabase.table("stores").select("id").eq("fulfillment_location_id", fulfillment_location_id).maybe_single().execute()
        if store_check.data:
            resolved_store_id = store_check.data["id"]
        # --- CRITICAL FIX END ---

        # Create Order
        order_payload = {
            "cart_id": cart["id"],
            "user_id": user_id,
            "status": "pending",
            "type": order_type,
            "total_amount": pricing["total"],
            "discount_amount": pricing["discount"],
            "delivery_address_id": address_id,
            "applied_promotion_id": pricing["promotion_id"],
            "store_id": resolved_store_id # Correctly resolved
        }
        
        order = supabase.table("orders").insert(order_payload).execute().data[0]

        # Order Items
        order_items_payload = [
            {
                "order_id": order["id"],
                "product_variant_id": i["variant_id"],
                "quantity": i["quantity"],
                "price_at_purchase": i["unit_price"],
                "fulfillment_location_id": fulfillment_location_id
            }
            for i in items
        ]
        supabase.table("order_items").insert(order_items_payload).execute()

        # Fulfillment Record
        supabase.table("fulfillments").insert({
            "order_id": order["id"],
            "fulfillment_location_id": fulfillment_location_id,
            "status": "pending",
            "fulfillment_type": order_type,
            "store_id": resolved_store_id
        }).execute()

        # 5. AI Context: Save Reasoning
        supabase.table("order_allocations").insert({
            "order_id": order["id"],
            "fulfillment_location_id": fulfillment_location_id,
            "allocation_type": allocation["allocation_type"],
            "reasoning": allocation["reasoning"]
        }).execute()

        # Update Cart Status
        supabase.table("carts").update({"status": "converted"}).eq("id", cart["id"]).execute()

        # Inventory Reservations
        for item in items:
             supabase.table("inventory_reservations").insert({
                "cart_id": cart["id"],
                "product_variant_id": item["variant_id"],
                "fulfillment_location_id": fulfillment_location_id,
                "quantity": item["quantity"],
                "status": "active",
                "expires_at": (datetime.utcnow() + timedelta(minutes=RESERVATION_TTL_MINUTES)).isoformat()
            }).execute()

        return {
            "order": order,
            "allocation": allocation,
            "agent_reason": allocation["reasoning"].get("explanation", "Order Allocated")
        }

    @staticmethod
    def _calculate_totals(items, promotion_code):
        subtotal = sum(i["unit_price"] * i["quantity"] for i in items)
        discount = 0.0
        promo_id = None
        if promotion_code:
            promo = supabase.table("promotions").select("*").eq("code", promotion_code).eq("is_active", True).maybe_single().execute().data
            if promo:
                promo_id = promo["id"]
                if promo["discount_type"] == "percentage": discount = subtotal * (promo["discount_value"] / 100)
                elif promo["discount_type"] == "fixed_amount": discount = promo["discount_value"]
                discount = min(discount, subtotal)
        return {"subtotal": subtotal, "discount": discount, "tax": subtotal * 0.05, "shipping": 0, "total": subtotal - discount, "promotion_id": promo_id}