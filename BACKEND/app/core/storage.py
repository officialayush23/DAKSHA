# app/core/storage.py

from app.core.database import supabase

class StorageService:
    @staticmethod
    def delete(bucket: str, paths: list[str]):
        """
        Delete files from Supabase Storage bucket.
        """
        if not paths:
            return
        supabase.storage.from_(bucket).remove(paths)
