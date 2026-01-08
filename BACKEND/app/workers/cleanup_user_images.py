# app/workers/cleanup_user_images.py

from datetime import datetime
from app.core.database import supabase
from app.core.storage import StorageService

def cleanup_expired_user_images():
    now = datetime.utcnow().isoformat()

    rows = (
        supabase
        .table("user_uploaded_images")
        .select("id, image_path")
        .lt("expires_at", now)
        .execute()
        .data
    )

    for row in rows:
        try:
            StorageService.delete(
                bucket="user_uploaded_image",
                paths=[row["image_path"]],
            )
        except Exception:
            pass

        supabase.table("user_uploaded_images") \
            .delete() \
            .eq("id", row["id"]) \
            .execute()
