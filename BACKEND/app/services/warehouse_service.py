# app/services/warehouse_service.py
from app.core.database import supabase
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
            
            # Use RPC for inventory adjustment
            from app.core.rpc import RPCService
            
            RPCService.adjust_inventory(
                variant_id=item['variant_id'],
                location_id=warehouse_id,
                delta=item['quantity'],
                reason="Inbound stock processing",
            )
            
            # Read back updated inventory
            updated = (
                supabase.table("inventory")
                .select("*")
                .eq("fulfillment_location_id", warehouse_id)
                .eq("product_variant_id", item['variant_id'])
                .maybe_single()
                .execute()
            ).data
            
            if updated:
                results.append(updated)
                
        return results