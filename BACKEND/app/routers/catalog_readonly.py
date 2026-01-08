# app/routers/catalog_readonly.py

from fastapi import APIRouter, Depends,Query
from app.core.database import supabase
from app.core.rbac import require_role

router = APIRouter(
    prefix="/catalog/read",
    tags=["Catalog: Read Only"]
)

# -----------------------------------
# READ PRODUCTS (STORE / WAREHOUSE)
# -----------------------------------
@router.get("/products")
async def list_products(
    active_only: bool = True,
    limit: int = Query(20, le=100),
    offset: int = 0,
     _rbac = Depends(
        require_role(
            "store_manager",
            "warehouse_manager",
            "catalog_admin",
            "support_agent",
            "fulfillment_agent",
            "super_admin",
        )
    ),
):
    q = (
        supabase.table("products")
        .select(
            "id, name, base_price, is_active, "
            "category_id, gender, usage_type, "
            "product_variants(count)"
        )
        .range(offset, offset + limit - 1)
    )

    if active_only:
        q = q.eq("is_active", True)

    return q.execute().data
# -----------------------------------
# READ VARIANTS FOR PRODUCT
# -----------------------------------
@router.get("/products/{product_id}")
async def get_product(product_id: str, _rbac = Depends(
        require_role(
            "store_manager",
            "warehouse_manager",
            "catalog_admin",
            "support_agent",
            "fulfillment_agent",
            "super_admin",
        )
    ),):
    res = (
        supabase.table("products")
        .select(
            "*, product_variants(*)"
        )
        .eq("id", product_id)
        .single()
        .execute()
    )
    return res.data
# -----------------------------------
@router.get("/variants/{variant_id}")
async def get_variant(variant_id: str, _rbac = Depends(
        require_role(
            "store_manager",
            "warehouse_manager",
            "catalog_admin",
            "support_agent",
            "fulfillment_agent",
            "super_admin",
        )
    ),):
    res = (
        supabase.table("product_variants")
        .select("*, products(name, is_active)")
        .eq("id", variant_id)
        .single()
        .execute()
    )
    return res.data
# -----------------------------------

@router.get("/unstocked/{fulfillment_location_id}")
async def unstocked_products(
    fulfillment_location_id: str,
    _rbac = Depends(
        require_role("store_manager", "warehouse_manager", "super_admin")
    ),
):

    res = supabase.rpc(
        "get_unstocked_variants_for_location",
        {"p_location_id": fulfillment_location_id}
    ).execute()

    return res.data or []
