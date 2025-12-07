from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus


class CommerceService:
    # ------------------ INVENTORY / LISTING ------------------ #

    @staticmethod
    def list_store_inventory(store_id: str, limit: int = 100, offset: int = 0):
        """
        Store inventory listing. Used by dashboards and potentially kiosk search.
        """
        res = (
            supabase.table("inventory")
            .select(
                "*, "
                "product_variants(sku, color_name, size_label, "
                "products(name))"
            )
            .eq("store_id", store_id)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data

    # ------------------ INVENTORY / STOCK ------------------ #

    @staticmethod
    def get_stock_by_sku(sku: str, store_id: str) -> dict:
        """
        Look up stock for a SKU at a specific store, including location details
        (aisle, bay, shelf, display_location, section_id).

        Returned shape is rich, but also backward-compatible with:
        - status / qty / reserved / location used in the old /inventory/check endpoint.
        """
        variant_res = (
            supabase.table("product_variants")
            .select("id, sku, color_name, size_label, products(name)")
            .eq("sku", sku)
            .single()
            .execute()
        )
        if not variant_res.data:
            raise HTTPException(status_code=404, detail="SKU not found")

        variant = variant_res.data
        variant_id = variant["id"]

        inv_res = (
            supabase.table("inventory")
            .select(
                "id, store_id, product_variant_id, quantity_on_hand, "
                "quantity_reserved, aisle_number, bay_number, shelf_height, "
                "display_location, section_id"
            )
            .eq("product_variant_id", variant_id)
            .eq("store_id", store_id)
            .maybe_single()
            .execute()
        )

        inv = inv_res.data

        if not inv:
            # No row => treat as zero stock
            return {
                "sku": variant["sku"],
                "product_name": variant["products"]["name"],
                "store_id": store_id,
                "available": False,
                "status": "out_of_stock",
                "quantity_on_hand": 0,
                "quantity_reserved": 0,
                "qty": 0,         # backward-compat
                "reserved": 0,    # backward-compat
                "location": None,
            }

        available = inv["quantity_on_hand"] > 0
        qty = inv["quantity_on_hand"]
        reserved = inv.get("quantity_reserved", 0)

        return {
            "sku": variant["sku"],
            "product_name": variant["products"]["name"],
            "store_id": store_id,
            "available": available,
            "status": "available" if available else "out_of_stock",
            "quantity_on_hand": qty,
            "quantity_reserved": reserved,
            "qty": qty,              # backward-compat
            "reserved": reserved,     # backward-compat
            "location": {
                "aisle_number": inv["aisle_number"],
                "bay_number": inv["bay_number"],
                "shelf_height": inv["shelf_height"],
                "display_location": inv["display_location"],
                "section_id": inv["section_id"],
            },
        }

    # ------------------ CART HELPERS ------------------ #

    @staticmethod
    def _get_or_create_cart(user_id: str) -> dict:
        cart = (
            supabase.table("carts")
            .select("id")
            .eq("user_id", user_id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        )
        if cart.data:
            return cart.data
        created = (
            supabase.table("carts")
            .insert({"user_id": user_id, "status": "active"})
            .execute()
        )
        return created.data[0]

    # ------------------ CART / CHECKOUT ------------------ #

    @staticmethod
    async def add_to_cart(user_id: str, variant_id: str, store_id: str, qty: int):
        # 1. Optimistic locking on inventory
        inv = (
            supabase.table("inventory")
            .select(
                "id, store_id, product_variant_id, "
                "quantity_on_hand, quantity_reserved, version"
            )
            .eq("product_variant_id", variant_id)
            .eq("store_id", store_id)
            .single()
            .execute()
        )

        if not inv.data or inv.data["quantity_on_hand"] < qty:
            raise HTTPException(400, "Insufficient Stock")

        updated_res = (
            supabase.table("inventory")
            .update(
                {
                    "quantity_on_hand": inv.data["quantity_on_hand"] - qty,
                    "quantity_reserved": inv.data.get("quantity_reserved", 0) + qty,
                    "version": inv.data["version"] + 1,
                }
            )
            .eq("id", inv.data["id"])
            .eq("version", inv.data["version"])
            .execute()
        )

        if not updated_res.data:
            raise HTTPException(409, "Stock changed concurrently. Please retry.")

        updated = updated_res.data[0]

        # 2. Realtime update to store dashboards
        await EventBus.notify_store_inventory(
            str(store_id),
            {
                "inventory_id": updated["id"],
                "product_variant_id": updated["product_variant_id"],
                "quantity_on_hand": updated["quantity_on_hand"],
                "quantity_reserved": updated["quantity_reserved"],
            },
        )

        # 3. Upsert into cart
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

    @staticmethod
    def get_cart_with_items(user_id: str):
        cart = (
            supabase.table("carts")
            .select("id, created_at")
            .eq("user_id", user_id)
            .eq("status", "active")
            .maybe_single()
            .execute()
        )
        if not cart.data:
            return None

        items = (
            supabase.table("cart_items")
            .select(
                "id, quantity, "
                "product_variants(id, price_override, product_id, "
                "products(base_price, name))"
            )
            .eq("cart_id", cart.data["id"])
            .execute()
        )
        return {"cart": cart.data, "items": items.data}

    @staticmethod
    def checkout(
        user_id: str,
        order_type: str,
        store_id: str | None,
        address_id: str | None,
        promotion_code: str | None,
    ):
        cart_data = CommerceService.get_cart_with_items(user_id)
        if not cart_data or not cart_data["items"]:
            raise HTTPException(400, "Cart is empty")

        items = cart_data["items"]
        total = 0.0
        for row in items:
            pv = row["product_variants"]
            base_price = float(pv["products"]["base_price"])
            price = float(pv["price_override"] or base_price)
            total += price * int(row["quantity"])

        discount = 0.0
        if promotion_code:
            promo_res = (
                supabase.table("promotions")
                .select("*")
                .eq("code", promotion_code)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )
            promo = promo_res.data
            if promo:
                if promo["discount_type"] == "percentage":
                    discount = total * float(promo["discount_value"]) / 100
                elif promo["discount_type"] == "fixed_amount":
                    discount = float(promo["discount_value"])
                discount = max(0.0, min(discount, total))

        order_res = (
            supabase.table("orders")
            .insert(
                {
                    "user_id": user_id,
                    "status": "pending",
                    "type": order_type,
                    "total_amount": total,
                    "discount_amount": discount,
                }
            )
            .execute()
        )
        order = order_res.data[0]

        order_items_payload = []
        for row in items:
            pv = row["product_variants"]
            base_price = float(pv["products"]["base_price"])
            price = float(pv["price_override"] or base_price)
            order_items_payload.append(
                {
                    "order_id": order["id"],
                    "product_variant_id": pv["id"],
                    "quantity": row["quantity"],
                    "price_at_purchase": price,
                }
            )

        supabase.table("order_items").insert(order_items_payload).execute()

        supabase.table("carts").update(
            {"status": "converted"}
        ).eq("id", cart_data["cart"]["id"]).execute()

        return order

    # ------------------ ORDER TRACKING ------------------ #

    @staticmethod
    def track_order(order_id: str) -> dict:
        """
        Basic tracking: order status + latest fulfillment info.
        """
        order_res = (
            supabase.table("orders")
            .select("*")
            .eq("id", order_id)
            .maybe_single()
            .execute()
        )
        if not order_res.data:
            raise HTTPException(status_code=404, detail="Order not found")

        order = order_res.data

        fulfill_res = (
            supabase.table("fulfillments")
            .select("*")
            .eq("order_id", order_id)
            .order("shipped_at", desc=True)
            .maybe_single()
            .execute()
        )

        fulfillment = fulfill_res.data

        return {
            "order_id": order_id,
            "status": order["status"],
            "type": order["type"],
            "total_amount": order["total_amount"],
            "discount_amount": order["discount_amount"],
            "latest_fulfillment": fulfillment,
        }
