from typing import List, Optional

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.management import PromotionCreate
from app.database import supabase

router = APIRouter(prefix="/admin/promotions", tags=["Admin: Promotions"])


@router.post("/promotions")
async def create_promotion(
    data: PromotionCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a promotion (coupon) according to the promotions table schema.
    promotions columns: code, name, discount_type, discount_value,
    constraints (jsonb), is_public, is_active, max_usage_global,
    current_usage_count, max_usage_per_user, applicable_store_ids, applicable_categories.
    """
    payload = {
        "code": data.code,
        "name": data.name,
        "discount_type": data.discount_type,       # discount_type_enum
        "discount_value": data.discount_value,
        "constraints": data.constraints,
        "max_usage_global": data.max_usage_global,
        "is_active": True,
        # rely on defaults: is_public=true, current_usage_count=0, max_usage_per_user=null
    }

    res = supabase.table("promotions").insert(payload).execute()
    return res.data[0]


@router.get("/promotions")
async def list_promotions(user_id: str = Depends(get_current_user_id)):
    """
    List all promotions. We *do not* order by created_at because schema
    does not define that column on promotions.
    """
    res = (
        supabase.table("promotions")
        .select("*")
        .order("code")  # stable, exists on schema
        .execute()
    )
    return res.data


@router.patch("/promotions/{promo_id}/status")
async def toggle_promotion(
    promo_id: str,
    is_active: bool,
    user_id: str = Depends(get_current_user_id),
):
    """
    Enable/disable a promotion.
    """
    res = (
        supabase.table("promotions")
        .update({"is_active": is_active})
        .eq("id", promo_id)
        .execute()
    )
    return {"status": "updated", "data": res.data[0] if res.data else None}


@router.post("/campaigns")
async def create_campaign(
    title: str,
    target_tags: Optional[List[str]] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    Create an ad_campaign row.
    ad_campaigns: (title, target_tags, target_gender, promoted_products, is_active, created_at)
    """
    res = (
        supabase.table("ad_campaigns")
        .insert(
            {
                "title": title,
                "target_tags": target_tags or [],
                "is_active": True,
            }
        )
        .execute()
    )
    return res.data[0]


@router.get("/campaigns")
async def list_campaigns(user_id: str = Depends(get_current_user_id)):
    """
    List all ad_campaigns ordered by created_at (exists on table).
    """
    res = (
        supabase.table("ad_campaigns")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data
