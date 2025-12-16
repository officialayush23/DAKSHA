import apiClient from '../lib/apiClient';

export const adminService = {
  // --- CATALOG MANAGEMENT ---
  
  // POST /admin/catalog/products
  createProduct: (productData) => {
    return apiClient.post('/admin/catalog/products', productData);
  },

  // POST /admin/catalog/variants
  createVariant: (variantData) => {
    return apiClient.post('/admin/catalog/variants', variantData);
  },

  // --- STORE OPERATIONS (HQ Level) ---

  // POST /admin/inventory/stores
  // Used to open a new physical store or warehouse location
  createStore: (storeData) => {
    return apiClient.post('/admin/inventory/stores', storeData);
  },

  // --- SUPPORT DESK ---

  // GET /admin/support/tickets
  getTickets: (status = 'open') => {
    return apiClient.get('/admin/support/tickets', {
      params: { status }
    });
  },

  // GET /admin/support/stats
  getSupportStats: () => {
    return apiClient.get('/admin/support/stats');
  },

  // PATCH /admin/support/tickets/{ticket_id}
  resolveTicket: (ticketId, resolutionNotes, status = 'resolved') => {
    return apiClient.patch(`/admin/support/tickets/${ticketId}`, null, {
      params: { 
        status, 
        resolution_notes: resolutionNotes 
      }
    });
  },

  // --- PROMOTIONS & MARKETING ---

  // POST /admin/promotions/promotions
  createPromotion: (promoData) => {
    return apiClient.post('/admin/promotions/promotions', promoData);
  },

  // GET /admin/promotions/promotions
  getPromotions: () => {
    return apiClient.get('/admin/promotions/promotions');
  },

  // PATCH /admin/promotions/promotions/{promo_id}/status
  togglePromotionStatus: (promoId, isActive) => {
    return apiClient.patch(`/admin/promotions/promotions/${promoId}/status`, null, {
      params: { is_active: isActive }
    });
  },

  // POST /admin/promotions/campaigns
  createCampaign: (campaignData) => {
    return apiClient.post('/admin/promotions/campaigns', campaignData);
  }
};
