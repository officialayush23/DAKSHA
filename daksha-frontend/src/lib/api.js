import axios from "axios";
import { supabase } from "./supabaseClient";

const API_URL = import.meta.env.VITE_BACKEND_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" }
});

// Interceptor: Attach Supabase Token to every request
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data?.session?.access_token;
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- API SERVICES ---

export const UserService = {
  // Products
  getProducts: (filters) => api.get('/user/products', { params: filters }),
  getTrending: () => api.get('/user/trending'),
  
  // Feed
  getRecommendationFeed: (intent) => api.get('/feed', { params: { intent } }),
  
  // Search
  search: (query) => api.post('/user/search', { query, channel: 'web' }),
  
  // Profile & Auth Sync
  register: (userData) => api.post('/user/register', userData),
  getProfile: () => api.get('/user/profile'),
  
  // Events
  trackEvent: (eventType, entityType, entityId, metadata) => 
    api.post('/user/event', { 
      event_type: eventType, 
      entity_type: entityType, 
      entity_id: entityId, 
      metadata 
    }),
    
  // Reviews (New)
  getReviews: (productId) => api.get(`/user/products/${productId}/reviews`),
  addReview: (data) => api.post('/user/reviews', data),
};

export const CartService = {
  getCart: () => api.get('/cart/'),
  addItem: (variantId, qty, sessionId) => api.post('/cart/items', { 
    product_variant_id: variantId, quantity: qty, session_id: sessionId 
  }),
};

export default api;