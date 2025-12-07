import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000', 
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token'); 
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const catalogService = {
  searchProducts: async (query, limit = 20) => {
    try {
      const q = query || "latest"; 
      const response = await api.get(`/catalog/search?q=${q}&limit=${limit}`);
      return response.data.results; 
    } catch (error) {
      console.error("Search failed", error);
      return [];
    }
  }
};

export const cartService = {
  addToCart: async (variantId, storeId, quantity = 1) => {
    try {
      const payload = {
        variant_id: variantId,
        store_id: storeId,
        quantity: quantity
      };
      const response = await api.post('/cart/add', payload);
      return response.data;
    } catch (error) {
      throw error; 
    }
  }
};

export default api;