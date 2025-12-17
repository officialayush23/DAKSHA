// src/lib/apiClient.js

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_BASE_URL || "http://localhost:8000",
});

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

export default api;
