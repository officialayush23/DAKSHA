# app/agents/workers/inventory_agent.py
from app.agents.base import BaseWorkerAgent
from app.services.store_service import StoreService

class InventoryAgent(BaseWorkerAgent):
    name = "inventory_agent"

    def run(self, lat: float, lng: float, limit: int = 5):
        stores = StoreService.find_nearest_stores(lat, lng, limit)
        self.log_run(None, "inventory_check", f"{len(stores)} stores")
        return stores
