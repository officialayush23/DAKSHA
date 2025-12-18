from app.database import supabase
from datetime import datetime

class WarehouseService:
    
    @staticmethod
    def get_dashboard_stats(warehouse_id: str):
        # 1. Total SKUs
        sku_count = supabase.table("inventory")\
            .select("id", count="exact", head=True)\
            .eq("fulfillment_location_id", warehouse_id)\
            .execute().count
            
        # 2. Pending Outbound (Orders assigned to this warehouse)
        pending_out = supabase.table("fulfillments")\
            .select("id", count="exact", head=True)\
            .eq("fulfillment_location_id", warehouse_id)\
            .eq("status", "pending")\
            .execute().count

        return {
            "total_skus": sku_count or 0,
            "pending_shipments": pending_out or 0,
            "capacity_utilization": 75 # Mock or calculation based on max_capacity
        }

    @staticmethod
    def get_inventory(warehouse_id: str):
        return (
            supabase.table("inventory")
            .select("*, product_variants(*, products(name))")
            .eq("fulfillment_location_id", warehouse_id)
            .execute()
        ).data or []

    @staticmethod
    def process_inbound(warehouse_id: str, items: list):
        """
        Bulk add stock (e.g. from Supplier).
        items = [{ variant_id, quantity }]
        """
        results = []
        for item in items:
            # Check if exists
            existing = supabase.table("inventory")\
                .select("id, quantity_on_hand")\
                .eq("fulfillment_location_id", warehouse_id)\
                .eq("product_variant_id", item['variant_id'])\
                .maybe_single().execute()
            
            if existing.data:
                new_qty = existing.data['quantity_on_hand'] + item['quantity']
                res = supabase.table("inventory").update({
                    "quantity_on_hand": new_qty,
                    # "last_restocked_at": datetime.utcnow().isoformat() # Uncomment if column exists
                }).eq("id", existing.data['id']).execute()
            else:
                res = supabase.table("inventory").insert({
                    "fulfillment_location_id": warehouse_id,
                    "product_variant_id": item['variant_id'],
                    "quantity_on_hand": item['quantity'],
                    # "last_restocked_at": datetime.utcnow().isoformat()
                }).execute()
            
            if res.data:
                results.append(res.data[0])
                
        return results