import apiClient from '../lib/apiClient';

export const authService = {
  // POST /auth/login-phone
  loginPhone: (phoneNumber, guestId = null) => {
    return apiClient.post('/auth/login-phone', {
      phone_number: phoneNumber,
      guest_id: guestId
    });
  },

  // GET /users/me
  // Returns the current user's profile and ROLE (Admin, Store Ops, Customer)
  getCurrentUser: () => {
    return apiClient.get('/users/me');
  },

  // PATCH /users/me
  updateProfile: (profileData) => {
    return apiClient.patch('/users/me', profileData);
  },

  // POST /users/register
  // Technically an update, but used for "Complete Profile" screen
  registerProfile: (profileData) => {
    return apiClient.post('/users/register', profileData);
  }
};
