from fastapi import Request, Depends, HTTPException, status
from app.core.auth import get_current_user_id
from app.database import supabase
from typing import List

# --------------------------------------------------
# ROLE CHECK (GLOBAL + SCOPED)
# --------------------------------------------------

def require_role(*required_roles: str):
    """
    Dependency to check if user has ANY of the required roles.
    Now accepts multiple arguments like: require_role("admin", "store_manager")
    """
    async def dependency(user_id: str = Depends(get_current_user_id)):
        # 1. Fetch User Roles
        res = supabase.table("user_roles").select("role").eq("user_id", user_id).execute()
        user_roles = [r['role'] for r in res.data] if res.data else []
        
        # 2. Check Role (Allow super_admin bypass)
        if "super_admin" in user_roles:
            return user_id
            
        # Check if user has ANY of the required roles
        # If no roles required (empty), allow access (or block, depending on policy. Here we block empty).
        if not required_roles:
             return user_id

        has_required = any(role in user_roles for role in required_roles)
        
        if not has_required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role(s): {', '.join(required_roles)}"
            )
        return user_id
    return dependency

def require_store_access(id_param_name: str = "store_id"):
    """
    Checks if user has access to the store_id in the path parameters.
    """
    async def dependency(request: Request, user_id: str = Depends(get_current_user_id)):
        # 1. Extract Store ID from Path (Preferred)
        store_id = request.path_params.get(id_param_name)
        
        # 2. Fallback: Check Query Params (if not in path)
        if not store_id:
            store_id = request.query_params.get(id_param_name)
            
        if not store_id:
            # If we can't find the ID, we assume the Route will handle the 404/422 validation.
            return user_id

        # 3. Check Permissions
        res = supabase.table("user_roles")\
            .select("role, store_id")\
            .eq("user_id", user_id)\
            .execute()
            
        roles_data = res.data or []
        
        # Super Admin Bypass
        if any(r['role'] == 'super_admin' for r in roles_data):
            return user_id

        # Specific Access Check
        has_access = any(r['role'] == 'store_manager' and str(r['store_id']) == str(store_id) for r in roles_data)
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this store."
            )
        
        return user_id
    return dependency

def require_warehouse_access(id_param_name: str = "warehouse_id"):
    """
    Checks if user has access to the warehouse_id in the path parameters.
    """
    async def dependency(request: Request, user_id: str = Depends(get_current_user_id)):
        warehouse_id = request.path_params.get(id_param_name)
        if not warehouse_id:
            warehouse_id = request.query_params.get(id_param_name)

        if not warehouse_id:
            return user_id

        res = supabase.table("user_roles")\
            .select("role, warehouse_id")\
            .eq("user_id", user_id)\
            .execute()
            
        roles_data = res.data or []
        
        if any(r['role'] == 'super_admin' for r in roles_data):
            return user_id

        has_access = any(r['role'] == 'warehouse_manager' and str(r['warehouse_id']) == str(warehouse_id) for r in roles_data)
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this warehouse."
            )
        
        return user_id
    return dependency