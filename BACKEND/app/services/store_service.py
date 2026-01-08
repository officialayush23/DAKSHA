# app/services/store_service.py

from app.core.database import supabase


class StoreService:
    @staticmethod
    def find_nearest_stores(lat: float, lng: float, limit: int = 5):
        """
        Calls Postgres RPC `find_nearest_stores` which uses PostGIS/ST_DistanceSphere.
        """
        res = supabase.rpc(
            "find_nearest_stores",
            {
                "p_lat": float(lat),
                "p_lng": float(lng),
                "p_limit": int(limit),
            },
        ).execute()

        return res.data or []
