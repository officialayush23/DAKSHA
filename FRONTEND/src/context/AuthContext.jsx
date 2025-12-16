// src/context/AuthContext.jsx

import React, { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import api, { setAuthToken } from "@/lib/apiClient";

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const syncBackend = async (accessToken) => {
    setAuthToken(accessToken);
    try {
      await api.post("/auth/sync");
    } catch (err) {
      console.error("auth/sync failed", err);
    }
  };

  const fetchProfile = async () => {
    try {
      const res = await api.get("/users/me");
      setProfile(res.data);
    } catch (err) {
      console.error("fetch profile failed", err);
    }
  };

  useEffect(() => {
    const init = async () => {
      const { data } = await supabase.auth.getSession();
      const currentSession = data.session;
      setSession(currentSession || null);
      setUser(currentSession?.user ?? null);

      const token = currentSession?.access_token || null;

      // 🔐 Log initial token (page load / refresh)
      if (token) {
        console.log("🔐 [INIT] Bearer token:", token);
      } else {
        console.log("🔐 [INIT] No token");
      }

      setAuthToken(token || null);

      if (token) {
        await syncBackend(token);
        await fetchProfile();
      }

      setLoading(false);
    };

    init();

    const { data: subscription } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        setSession(newSession);
        setUser(newSession?.user ?? null);

        const token = newSession?.access_token || null;

        // 🔐 Log on every auth state change
        console.log(`🔐 [AUTH EVENT: ${event}] token:`, token || "NULL");

        setAuthToken(token || null);

        if (token) {
          await syncBackend(token);
          await fetchProfile();
        } else {
          setProfile(null);
        }
      }
    );

    return () => {
      subscription.subscription.unsubscribe();
    };
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) {
      setLoading(false);
      throw error;
    }
    const accessToken = data.session?.access_token;

    // 🔐 Log on explicit login call
    console.log("🔐 [LOGIN] Bearer token:", accessToken || "NULL");

    if (accessToken) {
      await syncBackend(accessToken);
      await fetchProfile();
    }
    setLoading(false);
  };

  const signUp = async (email, password) => {
    setLoading(true);
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) {
      setLoading(false);
      throw error;
    }
    setLoading(false);
  };

  const logout = async () => {
    await supabase.auth.signOut();
    setAuthToken(null);
    setSession(null);
    setUser(null);
    setProfile(null);
    console.log("🔐 [LOGOUT] Cleared token");
  };

  const refreshProfile = async () => {
    await fetchProfile();
  };

  const value = {
    session,
    user,
    profile,
    loading,
    login,
    signUp,
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
