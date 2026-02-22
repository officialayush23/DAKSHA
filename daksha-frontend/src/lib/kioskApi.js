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

// --- Kiosk Service ---
export const KioskService = {

  // ==========================================
  // SESSION
  // ==========================================

  // Check if Session is Active
  checkSessionStatus: () =>
    apiClient('/session/active', 'GET'),

  // Start New Session
  startSession: (channel = 'kiosk') =>
    apiClient('/session/start', 'POST', null, { channel }),

  // FIX: Phone login — replaces QR flow. POST /kiosk/login
  login: (phone, kiosk_id) => {
  console.log("Login payload:", { phone, kiosk_id });
  return apiClient('/kiosk/login', 'POST', { phone, kiosk_id });
},

listStores: () =>
  apiClient('/kiosk/stores', 'GET'),

listKiosksForStore: (store_id) =>
  apiClient(`/kiosk/stores/${store_id}/kiosks`, 'GET'),
  // ==========================================
  // CATALOG & SHOPPING
  // ==========================================

  // Browse Products
  listProducts: (limit = 50, category = null, search = null) =>
    apiClient('/products', 'GET', null, { limit, category, q: search }),

  // Product Detail — variants are inside response.variants
  getProductDetail: (productId) =>
    apiClient(`/products/${productId}`, 'GET'),

  // Similar Products
  getSimilarProducts: (productId) =>
    apiClient(`/products/${productId}/similar`, 'GET'),

  // ==========================================
  // CART & CHECKOUT
  // ==========================================

  // FIX: /user/cart → /cart
  getCart: () =>
    apiClient('/cart', 'GET'),

  // FIX: /user/cart/items → /cart/items + session_id as query param
  addToCart: (variantId, quantity = 1, session_id) =>
    apiClient('/cart/items', 'POST', { product_variant_id: variantId, quantity }, { session_id }),

  // FIX: /user/cart/items → /cart/items + session_id as query param
  updateCartItem: (variantId, quantity, session_id) =>
    apiClient(`/cart/items/${variantId}`, 'PUT', { quantity }, { session_id }),

  // FIX: /user/cart/items → /cart/items + session_id as query param
  removeCartItem: (variantId, session_id) =>
    apiClient(`/cart/items/${variantId}`, 'DELETE', null, { session_id }),

  // FIX: was missing /resume suffix
  resumeCheckout: (checkoutId) =>
    apiClient(`/kiosk/checkout/${checkoutId}/resume`, 'GET'),

  // Start Checkout
  startCheckout: () =>
    apiClient('/checkout/start', 'POST'),

  

  // ==========================================
  // PAYMENT
  // ==========================================

  processPayment: (checkoutId) =>
    apiClient(`/payment/pay/${checkoutId}`, 'POST'),
};



