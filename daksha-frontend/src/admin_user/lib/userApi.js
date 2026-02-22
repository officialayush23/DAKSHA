// daksha-frontend\src\admin_user\lib\userApi.js
import { apiClient } from '../../lib/adminApi';

export const UserAdminService = {
  // ==============================
  // 👥 USER LIST & PROFILE
  // ==============================
  
  // Matches @router.get("") in admin_user.py
  listUsers: (limit = 50, offset = 0) => 
    apiClient('/admin/users', 'GET', null, { limit, offset }),

  // Matches @router.get("/{user_id}/profile")
  getUserProfile: (userId) => 
    apiClient(`/admin/users/${userId}/profile`, 'GET'),

  // Matches @router.get("/{user_id}/spend")
  getUserSpend: (userId) => 
    apiClient(`/admin/users/${userId}/spend`, 'GET'),

  // ==============================
  // 📦 ORDERS & PICKUPS
  // ==============================

  // Matches @router.get("/{user_id}/orders")
  getUserOrders: (userId) => 
    apiClient(`/admin/users/${userId}/orders`, 'GET'),

  // Matches @router.get("/{user_id}/pickups")
  getUserPickups: (userId) => 
    apiClient(`/admin/users/${userId}/pickups`, 'GET'),

  // Matches @router.patch("/{user_id}/orders/{order_id}/status")
  updateOrderStatus: (userId, orderId, status, reason) =>
    apiClient(`/admin/users/${userId}/orders/${orderId}/status`, 'PATCH', { status }, { reason }),

  // ==============================
  // 🏷️ LOYALTY & COUPONS
  // ==============================

  // Matches @router.get("/{user_id}/loyalty")
  getUserLoyalty: (userId) => 
    apiClient(`/admin/users/${userId}/loyalty`, 'GET'),

  // Matches @router.get("/{user_id}/coupons/personalized")
  getUserPersonalizedCoupons: (userId) => 
    apiClient(`/admin/users/${userId}/coupons/personalized`, 'GET'),

  // Reuses global coupon creation for issuing rewards
  createPersonalizedOffer: (userId, data) =>
    apiClient('/admin/users/coupons', 'POST', data, { reason: 'personalized_reward' }),

  // ==============================
  // 🤝 SUPPORT & ACTIVITY
  // ==============================

  // Matches @router.get("/{user_id}/complaints")
  getUserComplaints: (userId) => 
    apiClient(`/admin/users/${userId}/complaints`, 'GET'),

  // Matches @router.patch("/{user_id}/complaints/{complaint_id}")
  updateComplaintStatus: (userId, complaintId, status, reason) =>
    apiClient(`/admin/users/${userId}/complaints/${complaintId}`, 'PATCH', { status }, { reason }),

  // Matches @router.get("/{user_id}/events") for Audit/Debug logs
  getUserEvents: (userId, limit = 100) => 
    apiClient(`/admin/users/${userId}/events`, 'GET', null, { limit }),
};