# # app/routers/admin_rbac.py

# from fastapi import APIRouter, Depends, HTTPException
# from app.core.rbac import require_role
# from app.database import supabase
# from app.models.rbac import RoleAssignRequest

# router = APIRouter(prefix="/admin/rbac", tags=["Admin: RBAC"])


# # -------------------------------
# # ASSIGN ROLE
# # -------------------------------
# @router.post("/assign")
# async def assign_role(
#     payload: RoleAssignRequest,
#     _rbac=Depends(require_role("super_admin")),
# ):
#     role = payload.role

#     # 🚫 HARD BLOCK GLOBAL IDENTITIES
#     if role in ("customer", "super_admin"):
#         raise HTTPException(
#             400,
#             "Global roles cannot be assigned via RBAC"
#         )

#     scoped_roles = {
#         "store_manager": "store_id",
#         "warehouse_manager": "warehouse_id",
#     }

#     if role in scoped_roles:
#         required = scoped_roles[role]
#         if not getattr(payload, required):
#             raise HTTPException(400, f"{required} required for {role}")

#     try:
#         exists_res = (
#             supabase.table("user_roles")
#             .select("id")
#             .eq("user_id", payload.user_id)
#             .eq("role", role)
#             .eq("store_id", payload.store_id)
#             .eq("warehouse_id", payload.warehouse_id)
#             .maybe_single()
#             .execute()
#         )
#     except Exception as e:
#         raise HTTPException(500, f"DB error while checking existing role: {str(e)}")

#     exists = exists_res.data

#     if exists:
#         raise HTTPException(409, "Role already assigned")

#     try:
#         res = (
#             supabase.table("user_roles")
#             .insert({
#                 "user_id": payload.user_id,
#                 "role": role,
#                 "store_id": payload.store_id,
#                 "warehouse_id": payload.warehouse_id,
#             })
#             .execute()
#         )
#     except Exception as e:
#         raise HTTPException(500, f"DB insert error: {str(e)}")

#     # Safely extract returned row(s)
#     role_data = None
#     if isinstance(res.data, list) and len(res.data) > 0:
#         role_data = res.data[0]
#     else:
#         role_data = res.data

#     return {"status": "assigned", "role": role_data}


# # -------------------------------
# # REVOKE ROLE
# # -------------------------------
# @router.delete("/revoke")
# async def revoke_role(
#     payload: RoleAssignRequest,
#     _rbac=Depends(require_role("super_admin")),
# ):
#     supabase.table("user_roles") \
#         .delete() \
#         .eq("user_id", payload.user_id) \
#         .eq("role", payload.role) \
#         .eq("store_id", payload.store_id) \
#         .eq("warehouse_id", payload.warehouse_id) \
#         .execute()

#     return {"status": "revoked"}


# # -------------------------------
# # USER RBAC SNAPSHOT
# # -------------------------------
# @router.get("/user/{user_id}")
# async def list_user_roles(
#     user_id: str,
#     _rbac=Depends(require_role("super_admin")),
# ):
#     user = (
#         supabase.table("users")
#         .select("id, full_name, role")
#         .eq("id", user_id)
#         .single()
#         .execute()
#     ).data

#     roles = (
#         supabase.table("user_roles")
#         .select("role, store_id, warehouse_id, created_at")
#         .eq("user_id", user_id)
#         .execute()
#     ).data

#     return {
#         "user": user,
#         "operational_roles": roles,
#     }


# # -------------------------------
# # ROLE METADATA (FRONTEND)
# # -------------------------------
# @router.get("/roles")
# async def list_assignable_roles(
#     _rbac=Depends(require_role("super_admin")),
# ):
#     return {
#         "global_identity": ["customer", "super_admin"],
#         "operational_roles": [
#             "catalog_admin",
#             "support_agent",
#             "fulfillment_agent",
#             "store_manager",
#             "warehouse_manager",
#         ],
#         "scoped": {
#             "store_manager": ["store_id"],
#             "warehouse_manager": ["warehouse_id"],
#         },
#     }


# app/routers/admin_super.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.database import supabase
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/admin/super", tags=["Super Admin"])

# --- SECURITY DEPENDENCY ---
async def verify_super_admin(user_id: str = Depends(get_current_user_id)):
    """
    Checks the 'users' table to see if the user's global role is 'super_admin'.
    """
    try:
        # 1. Fetch the user's role from the main 'users' table
        res = supabase.table("users").select("role").eq("id", user_id).limit(1).execute()
        
        if not res.data:
            print(f"❌ User {user_id} not found in 'users' table.")
            raise HTTPException(403, "Access Denied: User profile not found.")

        user_role = res.data[0]['role']
        
        # 2. Check if the role is super_admin
        # (You can add 'admin' here too if you want them to have access)
        if user_role not in ["super_admin", "admin"]:
            print(f"⛔ Access Denied: User role is '{user_role}', required 'super_admin'")
            raise HTTPException(403, "Access Denied: Super Admin Privileges Required")
            
        return user_id

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"⚠️ Auth Check Error: {e}")
        raise HTTPException(403, "Authorization Failed")
    
# --- SCHEMAS ---
class LocationCreate(BaseModel):
    name: str
    type: str # 'store' or 'warehouse'
    city: str
    address_line_1: str
    latitude: float
    longitude: float
    # Store specific
    store_code: Optional[str] = None
    # Warehouse specific
    warehouse_code: Optional[str] = None

class RoleAssign(BaseModel):
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None

class RoleRevoke(BaseModel):
    user_id: str
    role: str
    store_id: Optional[str] = None
    warehouse_id: Optional[str] = None

# =========================================================
# 1. CREATE LOCATION (Store / Warehouse)
# =========================================================
@router.post("/locations")
async def create_location(data: LocationCreate, admin = Depends(verify_super_admin)):
    try:
        if data.type == 'store':
            payload = {
                "name": data.name,
                "store_code": data.store_code, # Mapping input to DB column 'code'
                "city": data.city,
                "address_line_1": data.address_line_1,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "is_active": True
            }
            res = supabase.table("stores").insert(payload).execute()
            return res.data[0]
            
        elif data.type == 'warehouse':
            # Assuming 'warehouses' table exists and has similar structure
            payload = {
                "name": data.name,
                "code": data.warehouse_code, # Add if your warehouse table has code
                "city": data.city,
                "address_line_1": data.address_line_1,
                "latitude": data.latitude,
                "longitude": data.longitude
            }
            res = supabase.table("warehouses").insert(payload).execute()
            return res.data[0]
            
        else:
            raise HTTPException(400, "Invalid location type")

    except Exception as e:
        print(f"Create Location Error: {e}")
        raise HTTPException(500, detail=str(e))

# =========================================================
# 2. ASSIGN ROLE
# =========================================================
# app/routers/admin_super.py

# ... imports ...
from uuid import UUID

def is_valid_uuid(val):
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False

@router.post("/roles")
async def assign_role(data: RoleAssign, admin = Depends(verify_super_admin)):
    try:
        # 1. Clean Inputs: Convert "string" or empty strings to None
        store_id = data.store_id if data.store_id and is_valid_uuid(data.store_id) else None
        warehouse_id = data.warehouse_id if data.warehouse_id and is_valid_uuid(data.warehouse_id) else None

        # 2. Check if role exists (using cleaned IDs)
        query = supabase.table("user_roles").select("id")\
            .eq("user_id", data.user_id)\
            .eq("role", data.role)
            
        if store_id:
            query = query.eq("store_id", store_id)
        if warehouse_id:
            query = query.eq("warehouse_id", warehouse_id)
            
        exists = query.execute()
        
        if exists.data:
            raise HTTPException(400, "User already has this role at this location.")

        payload = {
            "user_id": data.user_id,
            "role": data.role,
            "store_id": store_id,
            "warehouse_id": warehouse_id
        }
        
        res = supabase.table("user_roles").insert(payload).execute()
        return res.data[0]

    except HTTPException as he:
        raise he
    except Exception as e:
        # Provide a cleaner error message if it's a UUID issue
        if "invalid input syntax for type uuid" in str(e):
            raise HTTPException(400, "Invalid ID format. Please provide a valid UUID.")
        raise HTTPException(500, detail=str(e))

# =========================================================
# 3. GET USER ROLES (For Verification)
# =========================================================
@router.get("/roles/{target_user_id}")
async def get_user_roles(target_user_id: str, admin = Depends(verify_super_admin)):
    try:
        res = supabase.table("user_roles").select("*").eq("user_id", target_user_id).execute()
        return res.data
    except Exception as e:
        return []

# =========================================================
# 4. REVOKE ROLE
# =========================================================
@router.post("/roles/revoke") # Using POST for complex delete logic usually safer/easier
async def revoke_role(data: RoleRevoke, admin = Depends(verify_super_admin)):
    try:
        query = supabase.table("user_roles").delete()\
            .eq("user_id", data.user_id)\
            .eq("role", data.role)
            
        if data.store_id:
            query = query.eq("store_id", data.store_id)
        elif data.warehouse_id:
            query = query.eq("warehouse_id", data.warehouse_id)
        else:
            # Global role revoke (like super_admin)
            query = query.is_("store_id", "null").is_("warehouse_id", "null")

        res = query.execute()
        return {"status": "revoked"}

    except Exception as e:
        raise HTTPException(500, detail=str(e))