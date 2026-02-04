# app/services/storage_service.py
import uuid
from supabase import create_client
from app.core.config import settings

supabase = create_client(
    settings.SUPABASE_URL.rstrip("/") + "/",  # fixes trailing slash warning
    settings.SUPABASE_SERVICE_ROLE_KEY,
)


def upload_product_image(file, content_type: str) -> str:
    file_bytes = file.read()
    file_name = f"{uuid.uuid4()}"

    try:
        # 🔥 upload — raises exception on failure
        supabase.storage.from_("product_image").upload(
            file_name,
            file_bytes,
            {
                "content-type": content_type,
                "upsert": False,
            },
        )
    except Exception as e:
        # real error handling
        raise RuntimeError(f"Supabase upload failed: {e}")

    # ✅ success path — build public URL
    public_url = supabase.storage.from_("product_image").get_public_url(
        file_name
    )

    return public_url
