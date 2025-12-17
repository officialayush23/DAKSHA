# app/services/product_service.py
from app.database import supabase
from fastapi import HTTPException


class ProductService:

    @staticmethod
    async def get_pdp(product_id: str) -> dict:
        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------
        product = (
            supabase.table("products")
            .select("*")
            .eq("id", product_id)
            .eq("is_active", True)
            .maybe_single()
            .execute()
        ).data

        if not product:
            raise HTTPException(404, "Product not found")

        # --------------------------------------------------
        # VARIANTS
        # --------------------------------------------------
        variants = (
            supabase.table("product_variants")
            .select(
                "id, sku, color_name, size_label, material, "
                "price_override, image_url"
            )
            .eq("product_id", product_id)
            .execute()
        ).data or []

        variant_ids = [v["id"] for v in variants]

        # --------------------------------------------------
        # INVENTORY (PER LOCATION)
        # --------------------------------------------------
        inventory_rows = (
            supabase.table("inventory")
            .select(
                "product_variant_id, quantity_on_hand, "
                "fulfillment_locations(id, name, type)"
            )
            .in_("product_variant_id", variant_ids)
            .gt("quantity_on_hand", 0)
            .execute()
        ).data or []

        inventory_map = {}
        for row in inventory_rows:
            vid = row["product_variant_id"]
            inventory_map.setdefault(vid, []).append({
                "fulfillment_location_id": row["fulfillment_locations"]["id"],
                "location_name": row["fulfillment_locations"]["name"],
                "location_type": row["fulfillment_locations"]["type"],
                "available_qty": row["quantity_on_hand"],
            })

        # --------------------------------------------------
        # REVIEWS
        # --------------------------------------------------
        reviews = (
            supabase.table("product_reviews")
            .select("rating")
            .eq("product_id", product_id)
            .execute()
        ).data or []

        avg_rating = (
            round(sum(r["rating"] for r in reviews) / len(reviews), 2)
            if reviews else None
        )

        # --------------------------------------------------
        # FINAL SHAPE
        # --------------------------------------------------
        return {
            "product": {
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "base_price": product["base_price"],
                "category_id": product["category_id"],
                "gender": product["gender"],
                "style_tags": product.get("style_tags") or [],
            },
            "variants": [
                {
                    "id": v["id"],
                    "sku": v["sku"],
                    "color_name": v["color_name"],
                    "size_label": v["size_label"],
                    "material": v["material"],
                    "price": float(v["price_override"] or product["base_price"]),
                    "image_url": v["image_url"],
                    "inventory": inventory_map.get(v["id"], []),
                }
                for v in variants
            ],
            "reviews": {
                "average_rating": avg_rating,
                "review_count": len(reviews),
            },
            "agent_context": {
                "inventory_strategy": "warehouse_first",
                "sellability": "high" if avg_rating and avg_rating >= 4 else "medium",
            },
        }
