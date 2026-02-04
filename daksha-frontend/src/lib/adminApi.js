import { supabase } from './supabaseClient'; 

// --- Base API Client ---
export const apiClient = async (endpoint, method = 'GET', data = null, params = {}) => {
  const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  
  const url = new URL(`${baseURL}${endpoint}`);
  Object.keys(params).forEach(key => {
    if (params[key] !== undefined && params[key] !== null) {
      url.searchParams.append(key, params[key]);
    }
  });

  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // Inject Supabase Token
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;

  if (token) {
    options.headers.Authorization = `Bearer ${token}`;
  }

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url.toString(), options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

// --- Admin Service ---
export const AdminService = {
  // ==========================================
  // 📦 PRODUCTS
  // ==========================================
  createProduct: (data) => 
    apiClient('/admin/products', 'POST', data),

  listProducts: (limit = 100, offset = 0) => 
    apiClient('/admin/products', 'GET', null, { limit, offset }),

  updateProduct: (id, data) => 
    apiClient(`/admin/products/${id}`, 'PUT', data),

  deleteProduct: (id) => 
    apiClient(`/admin/products/${id}`, 'DELETE'),

  // ==========================================
  // 🎨 VARIANTS
  // ==========================================
  createVariant: (data) => 
    apiClient('/admin/variants', 'POST', data),

  updateVariant: (id, data) => 
    apiClient(`/admin/variants/${id}`, 'PUT', data),

  deleteVariant: (id) => 
    apiClient(`/admin/variants/${id}`, 'DELETE'),

  addImage: (id, data) => 
    apiClient(`/admin/variants/${id}/images`, 'POST', data),

  listVariants: (productId) => 
    apiClient(`/admin/products/${productId}/variants`, 'GET'),

  // ==========================================
  // 🏪 STORES
  // ==========================================
  listStores: () => 
    apiClient('/admin/stores', 'GET'),

  createStore: (data) => 
    apiClient('/admin/stores', 'POST', data),

  updateStore: (id, data) => 
    apiClient(`/admin/stores/${id}`, 'PUT', data),

  getStoreKpis: (id) => 
    apiClient(`/admin/stores/${id}/kpis`, 'GET'),

  listStorePickups: (id) => 
    apiClient(`/admin/stores/${id}/pickups`, 'GET'),

  // ==========================================
  // 📦 INVENTORY (MANAGE & VIEW)
  // ==========================================
  // 1. Manage (POST)
  assignGlobalInventory: (data) => 
    apiClient('/admin/inventory/global', 'POST', data),

  assignStoreInventory: (data) => 
    apiClient('/admin/inventory/store', 'POST', data),

  // 2. View (GET)
  getInventoryKpis: () => 
    apiClient('/admin/inventory/kpis', 'GET'),

  getGlobalInventoryItem: (productId) => 
    apiClient(`/admin/inventory/global/${productId}`, 'GET'),

  getStoreInventoryItem: (storeId, productId) => 
    apiClient(`/admin/inventory/store/${storeId}/${productId}`, 'GET'),

  // ==========================================
  // 🚚 ORDERS & PICKUPS
  // ==========================================
  updatePickup: (id, data) => 
    apiClient(`/admin/pickups/${id}`, 'PUT', data),

  updateDelivery: (id, data) => 
    apiClient(`/admin/orders/${id}/status`, 'PUT', data),

  getOrder: (id) => 
    apiClient(`/admin/orders/${id}`, 'GET'),

  // ==========================================
  // 🚚 DELIVERY ORDERS (NEW)
  // ==========================================
  getDeliveryOrders: (status = null) => 
    apiClient('/admin/delivery/orders', 'GET', null, { status }),

  getDeliveryOrderDetail: (orderId) => 
    apiClient(`/admin/delivery/orders/${orderId}`, 'GET'),

  updateDeliveryOrderStatus: (orderId, data) => 
    apiClient(`/admin/delivery/orders/${orderId}/status`, 'POST', data),

  // ==========================================
  // 💬 CHAT HANDOFFS (NEW)
  // ==========================================
  getChatHandoffs: () => 
    apiClient('/admin/chat/handoffs', 'GET'),

  // ==========================================
  // 🏷️ OFFERS
  // ==========================================
  listOffers: () => 
    apiClient('/admin/offers', 'GET'),

  createOffer: (data) => 
    apiClient('/admin/offers', 'POST', data),

  updateOffer: (id, data) => 
    apiClient(`/admin/offers/${id}`, 'PUT', data),

  deleteOffer: (id) => 
    apiClient(`/admin/offers/${id}`, 'DELETE'),

  // ==========================================
  // 🤝 SUPPORT & COMPLAINTS
  // ==========================================
  getHandoffs: () => 
    apiClient('/admin/handoffs', 'GET'),

  listComplaints: () => 
    apiClient('/admin/complaints', 'GET'),

  updateComplaint: (id, data) => 
    apiClient(`/admin/complaints/${id}`, 'PUT', data),

    // ==========================================
  // ↩️ RETURNS
  // ==========================================
  listReturns: () => 
    apiClient('/admin/returns', 'GET'),

  // Note: Status is passed as a query param { status: 'approved' }
  updateReturn: (id, status) => 
    apiClient(`/admin/returns/${id}`, 'PATCH', null, { status }),

  // ==========================================
  // 📊 DASHBOARD STATS
  // ==========================================
  getDashboardStats: async () => {
    const [inventoryKpis, stores, complaints, offers] = await Promise.allSettled([
      apiClient('/admin/inventory/kpis', 'GET'),
      apiClient('/admin/stores', 'GET'),
      apiClient('/admin/complaints', 'GET'),
      apiClient('/admin/offers', 'GET'),
 ]);
    return {
      inventory: inventoryKpis.status === 'fulfilled' ? inventoryKpis.value : null,
      stores: stores.status === 'fulfilled' ? stores.value : [],
      complaints: complaints.status === 'fulfilled' ? complaints.value : [],
      offers: offers.status === 'fulfilled' ? offers.value : [],
    };
  },
};