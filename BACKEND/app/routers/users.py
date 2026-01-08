# app/routers/users.py

from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id
from app.schemas.schemas import UserProfileUpdate, PaymentMethodCreate
from app.services.user_service import UserService
from fastapi import HTTPException
from app.core.database import supabase

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """
    Returns the current user's profile.
    If the row doesn't exist in public.users yet, it will be created.
    """
    profile = await UserService.ensure_user_exists(user_id)
    return profile


@router.patch("/me")
async def update_my_profile(
    data: UserProfileUpdate, user_id: str = Depends(get_current_user_id)
):
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    return await UserService.update_profile(user_id, update_data)


@router.post("/payment-methods")
async def add_payment_method(
    data: PaymentMethodCreate, user_id: str = Depends(get_current_user_id)
):
    return await UserService.add_payment_method(
        user_id, data.gateway_token_id, data.card_last4, data.card_brand
    )


@router.post("/register")
async def register_profile(
    data: UserProfileUpdate, user_id: str = Depends(get_current_user_id)
):
    """
    Called from frontend 'Complete Profile' screen.
    Semantically 'registration', technically it's just an update on public.users.
    """
    # Ensure row exists (in case /auth/sync wasn't called or failed)
    await UserService.ensure_user_exists(user_id)

    update_data = {k: v for k, v in data.dict().items() if v is not None}
    return await UserService.update_profile(user_id, update_data)


@router.get("/me/operational-role")
async def get_my_operational_roles(user_id: str = Depends(get_current_user_id)):
    """
    Return operational roles assigned to the current user.
    """
    rows = (
        supabase.table("user_roles")
        .select("role, store_id, warehouse_id, created_at")
        .eq("user_id", user_id)
        .execute()
    ).data or []

    return {"operational_roles": rows}


@router.get("/me/stores")
def get_my_stores(user_id: str = Depends(get_current_user_id)):
    """
    Returns a list of all stores assigned to the current user via the user_roles table.
    """
    try:
        # 1. Select store_id from user_roles where user_id matches
        # 2. Join with the 'stores' table to get name, code, etc.
        response = supabase.table("user_roles").select(
            "store_id, stores(id, name, store_code, is_active, city)"
        ).eq("user_id", user_id).not_.is_("store_id", "null").execute()

        # 3. Format the data for the frontend
        stores = []
        for item in response.data:
            if item.get('stores'):
                store_data = item['stores']
                stores.append({
                    "id": store_data['id'],
                    "name": store_data['name'],
                    "code": store_data['store_code'],
                    "city": store_data['city'],
                    "is_active": store_data['is_active']
                })
        
        return stores

    except Exception as e:
        print(f"Error fetching user stores: {e}")
        raise HTTPException(status_code=500, detail="Could not load assigned stores.")


@router.get("/me/addresses")
async def get_my_addresses(user_id: str = Depends(get_current_user_id)):
    """Get all addresses for the current user"""
    try:
        addresses = (
            supabase.table("user_addresses")
            .select("*")
            .eq("user_id", user_id)
            .order("is_default", desc=True)
            .execute()
        ).data or []
        
        return {"addresses": addresses}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch addresses: {str(e)}")


@router.post("/me/addresses")
async def add_address(
    payload: dict,
    user_id: str = Depends(get_current_user_id)
):
    """Add a new address for the current user"""
    try:
        # In Supabase v2, insert() already returns data - no need for .select()
        address = (
            supabase.table("user_addresses")
            .insert({
                "user_id": user_id,
                **payload
            })
            .execute()
        ).data[0]
        
        return {"address": address}
    except Exception as e:
        raise HTTPException(500, f"Failed to add address: {str(e)}")


@router.get("/me/payment-methods")
async def get_my_payment_methods(user_id: str = Depends(get_current_user_id)):
    """Get all payment methods for the current user"""
    try:
        methods = (
            supabase.table("user_payment_methods")
            .select("*")
            .eq("user_id", user_id)
            .order("is_default", desc=True)
            .execute()
        ).data or []
        
        return {"payment_methods": methods}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch payment methods: {str(e)}")


@router.get("/me/notifications")
async def get_my_notifications(
    user_id: str = Depends(get_current_user_id),
    limit: int = 50
):
    """Get recent notifications for the current user"""
    try:
        notifications = (
            supabase.table("user_notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch notifications: {str(e)}")


@router.delete("/me/addresses/{address_id}")
async def delete_address(
    address_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete an address for the current user"""
    try:
        # Verify ownership
        address = (
            supabase.table("user_addresses")
            .select("id")
            .eq("id", address_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        ).data
        
        if not address:
            raise HTTPException(404, "Address not found")
        
        supabase.table("user_addresses").delete().eq("id", address_id).execute()
        
        return {"status": "deleted", "address_id": address_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete address: {str(e)}")


@router.delete("/me/payment-methods/{method_id}")
async def delete_payment_method(
    method_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a payment method for the current user"""
    try:
        # Verify ownership
        method = (
            supabase.table("user_payment_methods")
            .select("id")
            .eq("id", method_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        ).data
        
        if not method:
            raise HTTPException(404, "Payment method not found")
        
        supabase.table("user_payment_methods").delete().eq("id", method_id).execute()
        
        return {"status": "deleted", "method_id": method_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete payment method: {str(e)}")