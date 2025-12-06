from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.models.management import PromotionCreate
from app.database import supabase

router = APIRouter(prefix="/admin/promotions", tags=["Admin: Promotions"])


@router.post("/promotions")
async def create_promotion(data: PromotionCreate, user_id: str = Depends(get_current_user_id)):
    res = supabase.table("promotions").insert({
        "code": data.code,
        "name": data.name,
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "constraints": data.constraints,
        "max_usage_global": data.max_usage_global,
        "is_active": True,
    }).execute()
    return res.data[0]


@router.get("/promotions")
async def list_promotions(user_id: str = Depends(get_current_user_id)):
    res = supabase.table("promotions").select("*").order("created_at", desc=True).execute()
    return res.data


@router.patch("/promotions/{promo_id}/status")
async def toggle_promotion(promo_id: str, is_active: bool, user_id: str = Depends(get_current_user_id)):
    res = supabase.table("promotions").update({"is_active": is_active}).eq("id", promo_id).execute()
    return {"status": "updated", "data": res.data[0] if res.data else None}


@router.post("/campaigns")
async def create_campaign(title: str, target_tags: list[str] = None):
    res = supabase.table("ad_campaigns").insert({
        "title": title,
        "target_tags": target_tags or [],
        "is_active": True,
    }).execute()
    return res.data[0]


@router.get("/campaigns")
async def list_campaigns():
    res = supabase.table("ad_campaigns").select("*").order("created_at", desc=True).execute()
    return res.data
