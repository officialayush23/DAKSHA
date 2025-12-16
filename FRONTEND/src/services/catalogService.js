import apiClient from "@/lib/apiClient";

export const catalogService = {
  // --- PRODUCTS ---

  searchProducts: async (query = "", limit = 20) => {
    // Endpoint: GET /catalog/search?q=...&limit=...
    const response = await apiClient.get("/catalog/search", {
      params: { q: query, limit },
    });
    return response.data;
  },

  createProduct: async (productData) => {
    // Endpoint: POST /admin/catalog/products
    const response = await apiClient.post("/admin/catalog/products", productData);
    return response.data;
  },

  getProductDetails: async (productId) => {
    // Endpoint: GET /admin/catalog/products/:id
    const response = await apiClient.get(`/admin/catalog/products/${productId}`);
    return response.data;
  },

  // --- VARIANTS ---

  createVariant: async (variantData) => {
    // Endpoint: POST /admin/catalog/variants
    const response = await apiClient.post("/admin/catalog/variants", variantData);
    return response.data;
  },

  deleteVariant: async (variantId) => {
    // Endpoint: DELETE /admin/catalog/variants/:id
    const response = await apiClient.delete(`/admin/catalog/variants/${variantId}`);
    return response.data;
  },

  // --- CATEGORIES ---

  getCategories: async () => {
    // Endpoint: GET /catalog/categories
    const response = await apiClient.get("/catalog/categories");
    return response.data;
  },

  createCategory: async (categoryData) => {
    // Endpoint: POST /admin/catalog/categories
    const response = await apiClient.post("/admin/catalog/categories", categoryData);
    return response.data;
  },

  deleteCategory: async (categoryId) => {
    // Endpoint: DELETE /admin/catalog/categories/:id
    const response = await apiClient.delete(`/admin/catalog/categories/${categoryId}`);
    return response.data;
  },

  // --- DASHBOARD & ANALYTICS ---

  getDashboardStats: async () => {
    // Endpoint: GET /admin/catalog/stats
    // Expected Return: { totalProducts: 100, totalVariants: 500, productsMissingImages: 5, topCategories: [] }
    const response = await apiClient.get("/admin/catalog/stats");
    return response.data;
  },

  getRecentProducts: async (limit = 5) => {
    // Endpoint: GET /admin/catalog/products/recent
    const response = await apiClient.get("/admin/catalog/products/recent", {
      params: { limit }
    });
    return response.data;
  },

  // --- UTILS ---

  uploadImage: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    // Endpoint: POST /uploads/product-image
    const response = await apiClient.post("/uploads/product-image", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data.public_url;
  }
};