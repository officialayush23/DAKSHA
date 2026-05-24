# app/services/storage_service.py
import uuid
from supabase import create_client
from app.core.config import settings

supabase = create_client(
    settings.SUPABASE_URL.rstrip("/") + "/",  # fixes trailing slash warning
    settings.SUPABASE_SERVICE_ROLE_KEY,
)


def upload_chat_image(file_bytes: bytes, content_type: str, original_name: str = "image") -> str:
    """Upload a user chat image to the user_uploaded_image bucket (bypasses RLS via service role).

    The bucket should be PRIVATE.  The returned URL encodes the bucket + path so
    that _inline_image() in chat.py can re-download the file via the service-role
    SDK client (supabase.storage.from_(bucket).download(path)) without needing
    direct public access.
    """
    import uuid, os
    ext = os.path.splitext(original_name)[1] or ".jpg"
    file_name = f"chat_{uuid.uuid4()}{ext}"

    try:
        supabase.storage.from_("user_uploaded_image").upload(
            file_name,
            file_bytes,
            {"content-type": content_type, "upsert": False},
        )
    except Exception as e:
        raise RuntimeError(f"Supabase chat image upload failed: {e}")

    # get_public_url() just constructs the canonical URL path:
    #   https://<project>.supabase.co/storage/v1/object/public/<bucket>/<file>
    # _inline_image() will parse this to extract bucket + filename and re-fetch
    # using the service-role SDK — so direct public access is never required.
    return supabase.storage.from_("user_uploaded_image").get_public_url(file_name)


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
