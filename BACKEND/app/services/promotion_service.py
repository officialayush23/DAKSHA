from app.database import supabase
from typing import List, Dict, Optional


class PromotionService:

    @staticmethod
    def get_active_promotions(limit: Optional[int] = None) -> List[dict]:
        query = (
            supabase.table("promotions")
            .select("*")
            .eq("is_active", True)
            .order("priority", desc=True)
        )

        if limit:
            query = query.limit(limit)

        res = query.execute()
        return res.data or []

    @staticmethod
    def applicable_promotions_for_product(
        product: dict,
        promotions: List[dict],
    ) -> List[dict]:

        applicable = []

        for p in promotions:
            constraints = p.get("constraints") or {}

            # Category filter
            if constraints.get("category_ids"):
                if product.get("category_id") not in constraints["category_ids"]:
                    continue

            # Gender filter
            if constraints.get("gender"):
                if product.get("gender") != constraints["gender"]:
                    continue

            # Tag filter
            if constraints.get("style_tags"):
                if not set(constraints["style_tags"]).intersection(
                    set(product.get("style_tags") or [])
                ):
                    continue

            applicable.append(p)

        return applicable
