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
  
  // Standard Catalog with filters
  listProducts: (filters) => api.get('/products', { params: filters }),
  
  getDetail: (id) => api.get(`/products/${id}`),
  
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
  get: () => api.get('/user/cart'),
  add: (variant_id, quantity = 1, session_id) => 
    api.post('/user/cart/items', { product_variant_id: variant_id, quantity }, { params: { session_id } }),
  update: (variant_id, quantity) => api.put(`/user/cart/items/${variant_id}`, { quantity }),
  remove: (variant_id) => api.delete(`/user/cart/items/${variant_id}`),
};

export const CheckoutService = {
  start: () => api.post('/checkout/start'),
  getStatus: (id) => api.get(`/checkout/${id}`),
  pay: (id, key) => api.post(`/payment/pay/${id}`, {}, { headers: { 'idempotency-key': key } }),
  getPickupOptions: (lat, lng, radius_km = 15) => 
    api.get('/checkout/pickup/stores', { params: { lat, lng, radius_km } }),
  resumeKiosk: (checkout_id) => api.get(`/kiosk/checkout/${checkout_id}`),
};

export const UserService = {
  getProfile: () => api.get('/user/profile'),
  updateProfile: (data) => api.put('/user/profile', data),
  getCompleteness: () => api.get('/user/profile/completeness'),
  
  // Addresses & Location Sync
  getAddresses: () => api.get('/user/addresses'),
  addAddress: (data) => api.post('/user/addresses', data),
  updateAddress: (id, data) => api.put(`/user/addresses/${id}`, data),
  
  // 🔥 Specific Location Patch API
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
  
  addToWishlist: (variantId) => api.post('/user/wishlist', { product_variant_id: variantId }),
  removeFromWishlist: (variantId) => api.delete(`/user/wishlist/${variantId}`),
};

export const OrderService = {
  getAll: () => api.get('/user/orders'),
  getDetail: (id) => api.get(`/user/orders/${id}`),
  requestReturn: (payload) => api.post('/support/returns', payload),
  requestExchange: (payload) => api.post('/support/exchanges', payload),
  fileComplaint: (payload) => api.post('/support/complaints', payload),
};

export const LoyaltyService = {
  getPoints: () => api.get('/loyalty/points'),
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