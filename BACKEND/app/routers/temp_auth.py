from fastapi import APIRouter, HTTPException
from app.schemas import UserRegisterRequest
from app.database import supabase
import uuid

router = APIRouter(prefix="/temp_auth", tags=["Temp Auth"])

@router.post("/register")
async def temp_register(payload: UserRegisterRequest):
    # This is a temporary endpoint to bypass phone number validation
    
    # Generate a new user_id
    user_id = str(uuid.uuid4())
    
    # Create a new user in the 'users' table
    try:
        # Create user in auth.users
        auth_user = supabase.auth.sign_up({
            "phone": payload.phone_number,
            "password": "password" # dummy password
        })
        
        if not auth_user or not auth_user.user:
            raise HTTPException(status_code=400, detail="Could not create user in auth")

        user_id = auth_user.user.id

        # Create user profile in 'profiles' table
        profile_data = {
            "id": user_id,
            "full_name": payload.full_name,
            "phone_number": payload.phone_number,
            "gender": payload.gender,
            "date_of_birth": str(payload.date_of_birth),
            "loyalty_tier": "Bronze",
            "loyalty_points": 0,
        }
        
        profile_response = supabase.table("profiles").insert(profile_data).execute()
        
        if len(profile_response.data) == 0:
            raise HTTPException(status_code=400, detail="Could not create user profile")

    except Exception as e:
        # If user already exists, try to get the user id
        try:
            user_response = supabase.table("users").select("id").eq("phone_number", payload.phone_number).execute()
            if len(user_response.data) > 0:
                user_id = user_response.data[0]['id']
            else:
                raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


    return {"user_id": user_id}
