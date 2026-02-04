import { supabase } from './supabaseClient'; 

// --- Base API Client (Same as Admin) ---
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

// --- Kiosk Service ---
export const KioskService = {
  // ==========================================
  // 🔐 SESSION & AUTH (QR CODE)
  // ==========================================
  
  // 1. Generate QR for Login Screen
  generateKioskQr: (kioskId) => 
    apiClient(`/kiosk/session/qr/${kioskId}`, 'GET'),

  // 2. Check if Session is Active (Polling)
  // Used by Login Screen to see if user scanned the QR
  checkSessionStatus: () => 
    apiClient('/session/active', 'GET'),

  // 3. Start New Anonymous Session
  startSession: (channel = 'kiosk') => 
    apiClient('/session/start', 'POST', null, { channel }),

  // ==========================================
  // 🛍️ CATALOG & SHOPPING
  // ==========================================
  
  // 1. Browse Products (Endless Aisle)
  listProducts: (limit = 50, category = null, search = null) => 
    apiClient('/products', 'GET', null, { limit, category, q: search }),

  // 2. Product Detail
  getProductDetail: (productId) => 
    apiClient(`/products/${productId}`, 'GET'),

  // 3. Check Global Inventory (For "Find Size" feature)
  checkGlobalInventory: (productId) => 
    apiClient(`/admin/inventory/global/${productId}`, 'GET'),

  // 4. Recommendations
  getSimilarProducts: (productId) => 
    apiClient(`/products/${productId}/similar`, 'GET'),

  // ==========================================
  // 🛒 CART & CHECKOUT
  // ==========================================
  
  // 1. Get Cart
  getCart: () => 
    apiClient('/user/cart', 'GET'),

  // 2. Add Item to Cart
  addToCart: (variantId, quantity = 1) => 
    apiClient('/user/cart/items', 'POST', { product_variant_id: variantId, quantity }),

  // 3. Update Cart Item
  updateCartItem: (variantId, quantity) => 
    apiClient(`/user/cart/items/${variantId}`, 'PUT', { quantity }),

  // 4. Remove Cart Item
  removeCartItem: (variantId) => 
    apiClient(`/user/cart/items/${variantId}`, 'DELETE'),

  // 5. Resume Mobile Checkout (Scan App QR at Kiosk)
  resumeCheckout: (checkoutId) => 
    apiClient(`/kiosk/checkout/${checkoutId}`, 'GET'),

  // 6. Start Checkout Process
  startCheckout: () => 
    apiClient('/checkout/start', 'POST'),

  // ==========================================
  // 💳 PAYMENT
  // ==========================================
  
  // 1. Process Payment (Terminal Integration)
  processPayment: (checkoutId) => 
    apiClient(`/payment/pay/${checkoutId}`, 'POST'),
};
