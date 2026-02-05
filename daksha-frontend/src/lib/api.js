// src/lib/api.js
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

// Helper for direct use in QueryFn
export const apiRequest = async (url, options = {}) => {
    const response = await api(url, options);
    return response.data;
};

// --- DOMAIN SERVICES ---

export const AuthService = {
  syncUser: (data) => api.post('/user/register', data),
};

export const ProductService = {
  getFeed: (filters) => api.get('/products', { params: filters }), 
  getDetail: (id) => api.get(`/products/${id}`),
  getSimilar: (id) => api.get(`/products/${id}/similar`),
  search: (query) => api.post('/user/search', { query, channel: 'web' }),
  addReview: (data) => api.post('/user/reviews', data),
  getReviews: (id) => api.get(`/user/products/${id}/reviews`),
};

export const CartService = {
  get: () => api.get('/user/cart'),
  add: (variant_id, quantity = 1, session_id) => 
    api.post('/user/cart/items', { product_variant_id: variant_id, quantity, session_id }),
  update: (variant_id, quantity) => api.put(`/user/cart/items/${variant_id}`, { quantity }),
  remove: (variant_id) => api.delete(`/user/cart/items/${variant_id}`),
};

export const CheckoutService = {
  start: () => api.post('/checkout/start'),
  getStatus: (id) => api.get(`/checkout/${id}`),
  pay: (id, key) => api.post(`/payment/pay/${id}`, {}, { headers: { 'idempotency-key': key } }),
  getPickupOptions: (lat, lng) => api.get('/checkout/pickup/stores', { params: { lat, lng } }),
  resumeKiosk: (checkout_id) => api.get(`/kiosk/checkout/${checkout_id}`),
};

export const UserService = {
  getProfile: () => api.get('/user/profile'),
  getAddresses: () => api.get('/user/addresses'),
  addAddress: (data) => api.post('/user/addresses', data),
  getOrders: () => api.get('/user/orders'),
  getOrderDetail: (id) => api.get(`/user/orders/${id}`),
  getLoyalty: () => api.get('/loyalty/points'),
};

export const AgentService = {
  sendMessage: (msg, channel = 'web') => api.post('/chat/message', { message: msg, channel }),
};

export default api;