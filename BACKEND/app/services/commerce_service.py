from fastapi import HTTPException
from app.database import supabase
from app.core.redis_bus import EventBus


class CommerceService:
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
        created = supabase.table("carts").insert(
            {"user_id": user_id, "status": "active"}
        ).execute()
        return created.data[0]

    @staticmethod
    async def add_to_cart(user_id: str, variant_id: str, store_id: str, qty: int):
        # 1. Optimistic locking on inventory
        inv = (
            supabase.table("inventory")
            .select("id, store_id, product_variant_id, quantity_on_hand, quantity_reserved, version")
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
                "id, quantity, product_variants(id, price_override, product_id, products(base_price, name))"
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
