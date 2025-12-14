# app/routers/admin_catalog_read.py

from fastapi import APIRouter, Depends
from app.database import supabase
from app.core.rbac import require_role

router = APIRouter(
    prefix="/admin/catalog/read",
    tags=["Admin: Catalog Read"]
)

# -----------------------------------
# LIST PRODUCTS
# -----------------------------------
@router.get("/products")
async def list_products(
    include_inactive: bool = False,
    _rbac=Depends(require_role("catalog_admin")),
):
    q = supabase.table("products").select(
        """
        id, name, base_price, is_active,
        category_id, gender, usage_type,
        created_at
        """
    )

    if not include_inactive:
        q = q.eq("is_active", True)

    return q.order("created_at", desc=True).execute().data


# -----------------------------------
# PRODUCT DETAIL (with variants)
# -----------------------------------
@router.get("/products/{product_id}")
async def product_detail(
    product_id: str,
    _rbac=Depends(require_role("catalog_admin")),
):
    product = (
        supabase.table("products")
        .select("*")
        .eq("id", product_id)
        .single()
        .execute()
    ).data

    variants = (
        supabase.table("product_variants")
        .select("*")
        .eq("product_id", product_id)
        .execute()
    ).data

    return {
        "product": product,
        "variants": variants,
    }


# -----------------------------------
# LIST VARIANTS (Global)
# -----------------------------------
@router.get("/variants")
async def list_variants(
    _rbac=Depends(require_role("catalog_admin")),
):
    return (
        supabase.table("product_variants")
        .select(
            """
            id, sku, product_id,
            color_name, size_label,
            material, price_override,
            created_at
            """
        )
        .order("created_at", desc=True)
        .execute()
        .data
    )


# -----------------------------------
# CATEGORY TREE
# -----------------------------------
@router.get("/categories")
async def list_categories(
    _rbac=Depends(require_role("catalog_admin")),
):
    return (
        supabase.table("categories")
        .select("id, name, parent_id")
        .execute()
        .data
    )
