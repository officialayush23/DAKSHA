import axios from "axios";
import { supabase } from "./supabaseClient";

const API_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" }
});

// Auto-attach Supabase Token
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const apiRequest = async (url, options = {}) => {
    const response = await api(url, options);
    return response.data;
};

// --- DOMAIN SERVICES ---

export const AuthService = {
  syncUser: (data) => api.post('/user/register', data),
};

export const ProductService = {
  // Smart Feed (Recommendation Engine)
  getFeed: (intent = null) => api.get('/recommendations/feed', { params: { intent } }),
  getTrending: () => api.get('/recommendations/trending'),
  
  // Standard Catalog with filters
  listProducts: (filters) => api.get('/products', { params: filters }),
  
  getDetail: (id) => api.get(`/products/${id}`),

  // FIX: was missing
  getSimilar: (id) => api.get(`/products/${id}/similar`),
  
  // Search (Logs intent & updates preferences)
  search: (query) => api.post('/user/search', { query, channel: 'web' }),
  
  // Reviews
  getReviews: (id) => api.get(`/user/products/${id}/reviews`),
  addReview: (data) => api.post('/user/reviews', data),
};

export const RecommendationService = {
  getSimilarVariants: (variantId) => api.get(`/recommendations/similar/${variantId}`),
  getBoughtTogether: (variantId) => api.get(`/recommendations/bought-together/${variantId}`),
  
};

export const CartService = {
  // FIX: /user/cart → /cart
  get: () => api.get('/cart'),

  // FIX: /user/cart/items → /cart/items, session_id added
  add: (variant_id, quantity = 1, session_id) => 
    api.post('/cart/items', { product_variant_id: variant_id, quantity }, { params: { session_id } }),

  // FIX: /user/cart/items → /cart/items, session_id added
  update: (variant_id, quantity, session_id) =>
    api.put(`/cart/items/${variant_id}`, { quantity }, { params: { session_id } }),

  // FIX: /user/cart/items → /cart/items, session_id added
  remove: (variant_id, session_id) =>
    api.delete(`/cart/items/${variant_id}`, { params: { session_id } }),
};

export const CheckoutService = {
  // 1. Start Checkout flows
  startDelivery: (data) => api.post('/checkout/delivery', data),
  startPickup: (data) => api.post('/checkout/pickup', data),
  
  // 2. Location / Stores for Pickup
  getPickupStores: (cart_id, lat, lng) => 
    api.get('/checkout/pickup/stores', { params: { cart_id, lat, lng } }),

  // 3. Coupons
  getCoupons: (checkout_id) => api.get(`/checkout/${checkout_id}/coupons`),
  applyCoupon: (checkout_id, data) => api.post(`/checkout/${checkout_id}/apply-coupon`, data),

  // 4. Finalize Checkout
  finalizeOrder: (checkout_id, data) => api.post(`/checkout/${checkout_id}/finalize`, data),

  // Legacy/Other routes kept for safety
  getStatus: (id) => api.get(`/checkout/${id}`),
  pay: (id, key) => api.post(`/payment/pay/${id}`, {}, { headers: { 'idempotency-key': key } }),
  resumeKiosk: (checkout_id) => api.get(`/kiosk/checkout/${checkout_id}/resume`),
};

export const UserService = {
  getProfile: () => api.get('/user/profile'),
  updateProfile: (data) => api.put('/user/profile', data),
  getCompleteness: () => api.get('/user/profile/completeness'),
  
  // Addresses & Location Sync
  getAddresses: () => api.get('/user/addresses'),
  addAddress: (data) => api.post('/user/addresses', data),
  updateAddress: (id, data) => api.put(`/user/addresses/${id}`, data),
  
  // FIX: was calling /user/ping instead of correct address location endpoint
  updateAddressLocation: (addressId, lat, lng) =>
    api.patch(`/user/addresses/${addressId}/location`, { lat, lng }),
  
  // Cards
  getCards: () => api.get('/user/cards'),
  addCard: (data) => api.post('/user/cards', data),
  removeCard: (id) => api.delete(`/user/cards/${id}`),
  
  // Events & Wishlist
  recomputePreferences: () => api.post('/user/preferences/recompute'),
  captureEvent: (eventType, entityType, entityId, metadata = {}) => 
    api.post('/user/event', null, { 
      params: { event_type: eventType, entity_type: entityType, entity_id: entityId },
      data: metadata 
    }),
  
  // FIX: getWishlist was missing
  getWishlist: () => api.get('/user/wishlist'),
  addToWishlist: (variantId) => api.post('/user/wishlist', { product_variant_id: variantId }),
  removeFromWishlist: (variantId) => api.delete(`/user/wishlist/${variantId}`),

  // FIX: these were missing
  getOffers: () => api.get('/user/offers'),
  getNotifications: (limit = 50) => api.get('/user/notifications', { params: { limit } }),
};

export const OrderService = {
  getAll: () => api.get('/user/orders'),
  getDetail: (id) => api.get(`/user/orders/${id}`),

  // FIX: was missing
  getFeedbackStatus: (id) => api.get(`/user/orders/${id}/feedback-status`),
};

export const SupportService = {
  // Returns
  requestReturn: (payload) => api.post('/support/returns', payload),
  // FIX: these were missing
  getMyReturns: (skip = 0, limit = 20) =>
    api.get('/support/returns/my-returns', { params: { skip, limit } }),
  getReturn: (returnId) => api.get(`/support/returns/${returnId}`),
  cancelReturn: (returnId, reason = null) =>
    api.patch(`/support/returns/${returnId}/cancel`, { reason }),

  // Complaints
  fileComplaint: (payload) => api.post('/support/complaints', payload),
  // FIX: these were missing
  getMyComplaints: (status = null, skip = 0, limit = 20) =>
    api.get('/support/complaints/my-complaints', { params: { status, skip, limit } }),
  getComplaint: (complaintId) => api.get(`/support/complaints/${complaintId}`),

  // Cancellations — FIX: these were missing
  requestCancellation: (orderId, reason = null) =>
    api.post(`/support/orders/${orderId}/cancel`, { reason }),
  getMyCancellations: (status = null, skip = 0, limit = 20) =>
    api.get('/support/cancellations/my-requests', { params: { status, skip, limit } }),

  // Exchanges
  requestExchange: (payload) => api.post('/support/exchanges', payload),
  // FIX: was missing
  getMyExchanges: (skip = 0, limit = 20) =>
    api.get('/support/exchanges/my-exchanges', { params: { skip, limit } }),
};

export const LoyaltyService = {
  // FIX: /loyalty/points → /loyalty/summary
  getSummary: () => api.get('/loyalty/summary'),
};

export const AgentService = {
  sendMessage: (msg, channel = 'web') => api.post('/chat/message', null, { params: { message: msg, channel } }),
};

export const SessionService = {
  start: (channel = 'web') => api.post('/session/start', null, { params: { channel } }),
  getActive: () => api.get('/session/active'),
  switchChannel: (channel) => api.post('/session/switch-channel', null, { params: { channel } }),
};

export default api;