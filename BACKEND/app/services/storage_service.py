# app/services/storage_service.py
# app/services/storage_service.py
import uuid
from supabase import create_client
from app.core.config import settings

supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY,  # service role only on backend
)

def upload_product_image(file, content_type: str):
    filename = f"{uuid.uuid4()}"
    path = f"variants/{filename}"

    supabase.storage.from_("product_image").upload(
        path,
        file,
        {"content-type": content_type},
    )

    public_url = supabase.storage.from_("product_image").get_public_url(path)
    return public_url
