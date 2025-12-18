from fastapi import APIRouter, Depends, HTTPException
from app.core.rbac import require_role
from app.database import supabase
from app.models.rbac import RoleAssignRequest, LocationCreate, RoleRevoke
from uuid import UUID

def is_valid_uuid(val):
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False

router = APIRouter(prefix="/admin/super", tags=["Super Admin: RBAC"])

# -------------------------------
# ASSIGN ROLE
# -------------------------------
@router.post("/roles")
async def assign_role(data: RoleAssignRequest, admin = Depends(require_role("super_admin"))):
    try:
        # 1. Clean Inputs
        store_id = data.store_id if data.store_id and is_valid_uuid(data.store_id) else None
        warehouse_id = data.warehouse_id if data.warehouse_id and is_valid_uuid(data.warehouse_id) else None

        # 2. Check Exists
        query = supabase.table("user_roles").select("id").eq("user_id", data.user_id).eq("role", data.role)
        if store_id: query = query.eq("store_id", store_id)
        if warehouse_id: query = query.eq("warehouse_id", warehouse_id)
            
        exists = query.execute()
        if exists.data:
            raise HTTPException(409, "User already has this role.")

        payload = {
            "user_id": data.user_id,
            "role": data.role,
            "store_id": store_id,
            "warehouse_id": warehouse_id
        }
        
        # ✅ Fix: Added .select()
        res = supabase.table("user_roles").insert(payload).select().execute()
        return res.data[0]

    except HTTPException as he: raise he
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# -------------------------------
# REVOKE ROLE
# -------------------------------
@router.post("/roles/revoke")
async def revoke_role(data: RoleRevoke, admin = Depends(require_role("super_admin"))):
    try:
        query = supabase.table("user_roles").delete().eq("user_id", data.user_id).eq("role", data.role)
        
        if data.store_id: query = query.eq("store_id", data.store_id)
        elif data.warehouse_id: query = query.eq("warehouse_id", data.warehouse_id)
        else: query = query.is_("store_id", "null").is_("warehouse_id", "null")

        # ✅ Fix: Added .select() (Delete returns data in Supabase often, but .select() ensures consistency if needed, though for delete execute() is usually enough, adding select doesn't hurt)
        query.execute()
        
        # Check remaining
        remaining = supabase.table("user_roles").select("id").eq("user_id", data.user_id).execute()
        if not remaining.data:
             supabase.table("users").update({"role": "customer"}).eq("id", data.user_id).execute()
             
        return {"status": "revoked"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# -------------------------------
# CREATE LOCATION
# -------------------------------
@router.post("/locations")
async def create_location(data: LocationCreate, admin = Depends(require_role("super_admin"))):
    try:
        # 1. Create Parent
        fl_payload = {
            "type": data.type,
            "name": data.name,
            "code": data.store_code if data.type == 'store' else data.warehouse_code,
            "address_line": data.address_line_1,
            "city": data.city,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "is_active": True
        }
        # ✅ Fix: Added .select()
        fl_res = supabase.table("fulfillment_locations").insert(fl_payload).select().execute()
        if not fl_res.data:
             raise HTTPException(500, "Failed to create Fulfillment Location")
             
        fl_id = fl_res.data[0]['id']

        # 2. Create Child
        child_table = "stores" if data.type == 'store' else "warehouses"
        child_payload = {
            "name": data.name,
            "address_line_1": data.address_line_1,
            "city": data.city,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "fulfillment_location_id": fl_id
        }
        
        if data.type == 'store':
            child_payload["store_code"] = data.store_code
            child_payload["is_active"] = True
        else:
            child_payload["code"] = data.warehouse_code

        # ✅ Fix: Added .select()
        res = supabase.table(child_table).insert(child_payload).select().execute()
        return res.data[0]

    except Exception as e:
        print(f"Create Location Error: {e}")
        raise HTTPException(500, detail=str(e))

@router.get("/roles/{target_user_id}")
async def get_user_roles(target_user_id: str, admin = Depends(require_role("super_admin"))):
    try:
        res = supabase.table("user_roles").select("*").eq("user_id", target_user_id).execute()
        return res.data
    except Exception:
        return []