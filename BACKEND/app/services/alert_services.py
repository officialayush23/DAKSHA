# app/services/alert_service.py
from app.database import supabase


class AlertService:

    @staticmethod
    def create_inventory_alert(
        fulfillment_location_id: str,
        variant_id: str,
        level: str,
        message: str
    ):
        return (
            supabase.table("inventory_alerts")
            .insert({
                "fulfillment_location_id": fulfillment_location_id,
                "product_variant_id": variant_id,
                "level": level,
                "message": message,
            })
            .execute()
        )
