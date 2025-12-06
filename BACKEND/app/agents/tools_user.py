from langchain.tools import tool
from app.services.user_service import UserService


@tool
async def update_user_profile_tool(user_id: str, field: str, value: str) -> str:
    """
    Update a user profile field (full_name, phone_number, gender, date_of_birth).
    """
    valid_fields = {"full_name", "phone_number", "gender", "date_of_birth"}
    if field not in valid_fields:
        return f"Error: Cannot update field '{field}'."

    try:
        await UserService.update_profile(user_id, {field: value})
        return f"Successfully updated {field} to {value}."
    except Exception as e:
        return f"Update failed: {str(e)}"
