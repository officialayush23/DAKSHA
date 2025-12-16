import apiClient from '../lib/apiClient';

export const inventoryService = {
  // --- DASHBOARD ---

  // GET /admin/inventory/dashboard/{store_id}
  // Note: Even though URL says 'admin', this is viewed by Store Managers
  getStoreDashboard: (storeId) => {
    return apiClient.get(`/admin/inventory/dashboard/${storeId}`);
  },

  // --- STOCK MANAGEMENT ---

  // GET /inventory/check
  // Check if a specific item exists in a specific location
  checkStock: (sku, fulfillmentLocationId) => {
    return apiClient.get('/inventory/check', {
      params: { 
        sku, 
        fulfillment_location_id: fulfillmentLocationId 
      }
    });
  },

  // PATCH /admin/inventory/update
  // Used when new stock arrives or stock is damaged/lost
  updateStock: (data) => {
    // data structure: { variant_id, store_id, quantity_on_hand, ... }
    return apiClient.patch('/admin/inventory/update', data);
  },

  // GET /inventory/nearby
  // Find stock in other stores (e.g., if current store is out of stock)
  findNearbyStock: (variantId, lat, lng, limit = 5) => {
    return apiClient.get('/inventory/nearby', {
      params: { 
        product_variant_id: variantId, 
        lat, 
        lng, 
        limit 
      }
    });
  }
};