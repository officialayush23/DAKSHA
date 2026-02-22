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
    apiClient('/admin/global/products?reason=admin_create_product', 'POST', data),

  listProducts: (limit = 100, offset = 0) =>
    apiClient('/admin/global/products', 'GET', null, { limit, offset }),

  updateProduct: (id, data) =>
    apiClient(`/admin/global/products/${id}?reason=admin_update_product_${id}`, 'PUT', data),

  deleteProduct: (id) =>
    apiClient(`/admin/global/products/${id}?reason=admin_delete_product_${id}`, 'DELETE'),

  // ==========================================
  // 🎨 VARIANTS
  // ==========================================
  createVariant: (data) =>
    apiClient('/admin/global/variants?reason=admin_create_variant', 'POST', data),

  updateVariant: (id, data) =>
    apiClient(`/admin/global/variants/${id}?reason=admin_update_variant_${id}`, 'PUT', data),

  deleteVariant: (id) =>
    apiClient(`/admin/global/variants/${id}?reason=admin_delete_variant_${id}`, 'DELETE'),

  addImage: (id, data) =>
    apiClient(`/admin/global/variants/${id}/images?reason=admin_add_image_to_variant_${id}`, 'POST', data),

  listVariants: (productId) =>
    apiClient(`/admin/global/products/${productId}/variants`, 'GET'),

  trainModel: () => 
    apiClient('/recommendations/train-model', 'POST'),

  // ==========================================
  // 🏪 STORES
  // ==========================================
  listStores: () =>
    apiClient('/admin/global/stores', 'GET'),

  createStore: (data) =>
  apiClient('/admin/global/stores', 'POST', data, { reason: 'admin_create_store' }),

  updateStore: (id, data) =>
    apiClient(`/admin/global/stores/${id}?reason=admin_update_store_${id}`, 'PUT', data),

  getStoreKpis: (id) =>
    apiClient(`/admin/global/stores/${id}/kpis`, 'GET'),

  listStorePickups: (id) =>
    apiClient(`/admin/global/stores/${id}/pickups`, 'GET'),

  // ==========================================
  // 📦 INVENTORY (MANAGE & VIEW)
  // ==========================================
  // 1. Manage (POST)
  assignGlobalInventory: (data) =>
    apiClient('/admin/global/inventory/global?reason=admin_assign_global_inventory', 'POST', data),

  assignStoreInventory: (data) =>
    apiClient('/admin/global/inventory/store?reason=admin_assign_store_inventory', 'POST', data),

  // 2. View (GET)
  getInventoryKpis: () =>
    apiClient('/admin/global/inventory/kpis', 'GET'),

  getGlobalInventoryItem: (productId) =>
    apiClient(`/admin/global/inventory/${productId}`, 'GET'),

  getStoreInventoryForVariant: (storeId, variantId) =>
    apiClient(`/admin/global/inventory/store/${storeId}/variant/${variantId}`, 'GET'),


  // ==========================================
  // 🚚 ORDERS & PICKUPS
  // ==========================================
  // ✅ Added listPickups here
  listPickups: () =>
    apiClient('/admin/global/pickups', 'GET'),

  updatePickup: (id, data) =>
    apiClient(`/admin/global/pickups/${id}?reason=admin_update`, 'PATCH', data),

  getOrder: (id) =>
    apiClient(`/admin/global/orders/${id}`, 'GET'),
 

  updateDelivery: (id, data) =>
    apiClient(`/admin/global/orders/${id}/status`, 'PUT', data),

  getOrder: (id) =>
    apiClient(`/admin/global/orders/${id}`, 'GET'),

  // ==========================================
  // 🚚 DELIVERY ORDERS (NEW)
  // ==========================================
  getDeliveryOrders: (status = null) =>
    apiClient('/admin/global/orders', 'GET', null, { status }),

  getDeliveryOrderDetail: (orderId) =>
    apiClient(`/admin/global/orders/${orderId}`, 'GET'),

  updateDeliveryOrderStatus: (orderId, data) =>
    apiClient(`/admin/global/orders/${orderId}/status?reason=admin_update_order_status`, 'POST', data),

  // ==========================================
  // 💬 CHAT HANDOFFS (NEW)
  // ==========================================
  getChatHandoffs: () =>
    apiClient('/admin/global/chat/handoffs', 'GET'),
  // ==========================================
  // 🖥️ KIOSKS
  // ==========================================
  listKiosks: () =>
    apiClient('/admin/global/kiosks', 'GET'),

  createKiosk: (data) =>
    apiClient('/admin/global/kiosks?reason=admin_create_kiosk', 'POST', data),
  // ==========================================
  // 🏷️ OFFERS
  // ==========================================
  listOffers: () =>
    apiClient('/admin/global/coupons', 'GET'),

  createOffer: (data) =>
    apiClient('/admin/global/coupons?reason=admin_create_coupon', 'POST', data),

  // Note: Your backend doesn't currently have PUT/DELETE for coupons in admin_global.py,
  // but if you add them later, they should look like this:
  updateOffer: (id, data) =>
    apiClient(`/admin/global/coupons/${id}?reason=admin_update_coupon_${id}`, 'PUT', data),

  deleteOffer: (id) =>
    apiClient(`/admin/global/coupons/${id}?reason=admin_delete_coupon_${id}`, 'DELETE'),
  // ==========================================
  // 🤝 SUPPORT & COMPLAINTS
  // ==========================================
  getHandoffs: () =>
    apiClient('/admin/global/handoffs', 'GET'),

  listComplaints: () =>
    apiClient('/admin/global/complaints', 'GET'),

  updateComplaint: (id, data) =>
    apiClient(`/admin/global/complaints/${id}`, 'PUT', data),

  // ==========================================
  // ↩️ RETURNS
  // ==========================================
  listReturns: () =>
    apiClient('/admin/global/returns', 'GET'),

  // Note: Status is passed as a query param { status: 'approved' }
  updateReturn: (id, status) =>
    apiClient(`/admin/global/returns/${id}`, 'PATCH', null, { status }),

  // ==========================================
  // 📉 DISCOUNT RULES (Automatic Sales)
  // ==========================================
  listDiscountRules: () =>
    apiClient('/admin/global/discount-rules', 'GET'),

  createDiscountRule: (data) =>
    apiClient('/admin/global/discount-rules?reason=admin_create_rule', 'POST', data),

  updateDiscountRule: (id, data) =>
    apiClient(`/admin/global/discount-rules/${id}?reason=admin_update_rule`, 'PUT', data),

  deleteDiscountRule: (id) =>
    apiClient(`/admin/global/discount-rules/${id}?reason=admin_delete_rule`, 'DELETE'),

  // ==========================================
  // 📊 DASHBOARD STATS
  // ==========================================
  getDashboardStats: async () => {
    const [inventoryKpis, stores, complaints, offers] = await Promise.allSettled([
      apiClient('/admin/global/inventory/kpis', 'GET'),
      apiClient('/admin/global/stores', 'GET'),
      apiClient('/admin/global/complaints', 'GET'),
      apiClient('/admin/global/coupons', 'GET'),
    ]);

  


    return {
      inventory: inventoryKpis.status === 'fulfilled' ? inventoryKpis.value : null,
      stores: stores.status === 'fulfilled' ? stores.value : [],
      complaints: complaints.status === 'fulfilled' ? complaints.value : [],
      offers: offers.status === 'fulfilled' ? offers.value : [],
    };
  },
};