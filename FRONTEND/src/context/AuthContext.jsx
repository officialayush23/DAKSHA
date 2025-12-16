import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient'; // Import the singleton
import api from '@/lib/apiClient'; // Your Axios instance

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Helper to log token for Swagger (Development only)
  const printTokenForSwagger = (session) => {
    if (session?.access_token) {
      console.log("%c📋 COPY THIS TOKEN FOR SWAGGER:", "color: yellow; font-size: 14px; font-weight: bold;");
      console.log(session.access_token); 
      console.log("%c-----------------------------------", "color: yellow;");
    }
  };

  useEffect(() => {
    // 1. Check active session on startup
    const checkSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        
        if (session) {
          console.log("✅ [Auth] Session found:", session.user.email);
          setUser(session.user);
          setToken(session.access_token);
          printTokenForSwagger(session); // Log on initial load
        } else {
          console.log("⚠️ [Auth] No active session");
        }
      } catch (error) {
        console.error("❌ [Auth] Error checking session:", error);
      } finally {
        setLoading(false); // CRITICAL: Runs to remove "Loading..." screen
      }
    };

    checkSession();

    // 2. Listen for auth changes (Login, Logout, etc.)
    const { data: authListener } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log(`🔐 [Auth Event]: ${event}`);
      
      if (session) {
        setUser(session.user);
        setToken(session.access_token);
        setLoading(false);
        printTokenForSwagger(session); // Log on updates (login/refresh)
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        setToken(null);
        setLoading(false);
      }
    });

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  // Helper to get token manually if needed
  const getToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  };

  const value = {
    user,
    token,         // Direct property access
    loading,
    getToken,      // Helper function access
    accessToken: token, 
    signIn: (data) => supabase.auth.signInWithPassword(data),
    signOut: () => supabase.auth.signOut(),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};