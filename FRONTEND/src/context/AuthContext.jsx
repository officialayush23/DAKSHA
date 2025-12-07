import React, { createContext, useContext, useEffect, useState } from "react";
import api, { setAuthToken } from "@/lib/apiClient";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const setToken = (newToken) => {
    setTokenState(newToken);
    if (newToken) {
      localStorage.setItem("token", newToken);
      setAuthToken(newToken);
    } else {
      localStorage.removeItem("token");
      setAuthToken(null);
    }
  };

  const fetchProfile = async () => {
    try {
      const res = await api.get("/users/me");
      setProfile(res.data);
    } catch (err) {
      console.error("fetch profile failed", err);
      setProfile(null);
    }
  };

  useEffect(() => {
    const init = async () => {
      const storedToken = localStorage.getItem("token");
      if (storedToken) {
        setToken(storedToken);
        await fetchProfile();
      }
      setLoading(false);
    };
    init();
  }, []);

  const logout = () => {
    setToken(null);
    setProfile(null);
  };

  const refreshProfile = async () => {
    await fetchProfile();
  };

  const value = {
    token,
    setToken,
    profile,
    loading,
    logout,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
