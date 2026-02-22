import { supabase } from './supabaseClient'; // Adjust path if necessary

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


// --- Admin User Service ---
export const AdminUserService = {
  // ==========================================
  // 👥 USERS DIRECTORY
  // ==========================================
  
  // List all users
  listUsers: (limit = 50, offset = 0) =>
    apiClient('/admin/users', 'GET', null, { limit, offset }),

  // Get User Profile
  getUserProfile: (userId) =>
    apiClient(`/admin/users/${userId}/profile`, 'GET'),

  // ==========================================
  // 🛍️ COMMERCE & ACTIVITY
  // ==========================================

  // Get User Sessions
  getUserSessions: (userId) =>
    apiClient(`/admin/users/${userId}/sessions`, 'GET'),

  // Get User Carts
  getUserCarts: (userId) =>
    apiClient(`/admin/users/${userId}/carts`, 'GET'),

  // Get User Orders
  getUserOrders: (userId) =>
    apiClient(`/admin/users/${userId}/orders`, 'GET'),

  // Update Order Status
  updateUserOrderStatus: (userId, orderId, data) =>
    apiClient(`/admin/users/${userId}/orders/${orderId}/status`, 'PATCH', data),

  // Get User Spend
  getUserSpend: (userId) =>
    apiClient(`/admin/users/${userId}/spend`, 'GET'),

  // Get User Events
  getUserEvents: (userId) =>
    apiClient(`/admin/users/${userId}/events`, 'GET'),

  // Get User Pickups
  getUserPickups: (userId) =>
    apiClient(`/admin/users/${userId}/pickups`, 'GET'),

  // Update Pickup
  updateUserPickup: (userId, pickupId, data) =>
    apiClient(`/admin/users/${userId}/pickups/${pickupId}`, 'PATCH', data),

  // ==========================================
  // 💎 LOYALTY & DISCOUNTS
  // ==========================================

  // Get User Loyalty Tier/Points
  getUserLoyalty: (userId) =>
    apiClient(`/admin/users/${userId}/loyalty`, 'GET'),

  // Get User Coupon Redemptions
  getUserCouponRedemptions: (userId) =>
    apiClient(`/admin/users/${userId}/coupons/redemptions`, 'GET'),

  // Get User Personalized Coupons
  getUserPersonalizedCoupons: (userId) =>
    apiClient(`/admin/users/${userId}/coupons/personalized`, 'GET'),

  // ==========================================
  // 🤖 AI AGENT DATA
  // ==========================================

  // Get Agent Runs for User
  getUserAgentRuns: (userId) =>
    apiClient(`/admin/users/${userId}/agents/runs`, 'GET'),

  // Get Agent Decisions made for User
  getUserAgentDecisions: (userId) =>
    apiClient(`/admin/users/${userId}/agents/decisions`, 'GET'),

  // ==========================================
  // 🎧 SUPPORT & FEEDBACK
  // ==========================================

  // Get User Complaints
  getUserComplaints: (userId) =>
    apiClient(`/admin/users/${userId}/complaints`, 'GET'),

  // Update Complaint Status
  updateUserComplaintStatus: (userId, complaintId, data) =>
    apiClient(`/admin/users/${userId}/complaints/${complaintId}`, 'PATCH', data),

  // Get User Reviews
  getUserReviews: (userId) =>
    apiClient(`/admin/users/${userId}/reviews`, 'GET'),
};