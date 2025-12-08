// src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

import { Button } from "@/components/ui/button";
import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { RegisterProfilePage } from "@/pages/RegisterProfile";
import AuthPage from "@/pages/AuthPage";
import ProductsPage from "@/pages/ProductsPage";

export default function App() {
  const { user, profile, logout, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        Loading...
      </div>
    );
  }

  const profileComplete =
    profile?.full_name && profile?.phone_number;

  return (
    <>
      <Routes>
        {!user && (
          <>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="*" element={<AuthPage />} />
          </>
        )}

        {user && !profileComplete && (
          <>
            <Route path="/register" element={<RegisterProfilePage />} />
            <Route path="*" element={<Navigate to="/register" replace />} />
          </>
        )}

        {user && profileComplete && (
          <>
            <Route path="/products" element={<ProductsPage />} />
            <Route path="*" element={<Navigate to="/products" replace />} />
          </>
        )}
      </Routes>

      {user && (
        <div className="fixed bottom-4 right-4 flex items-center gap-3 bg-background/90 border border-border rounded-full px-4 py-2 shadow-sm">
          <span className="text-xs text-muted-foreground max-w-[140px] truncate">
            {profile?.full_name || user.email}
          </span>
          <Button
            size="sm"
            variant="outline"
            className="text-xs px-3"
            onClick={logout}
          >
            Logout
          </Button>
        </div>
      )}
    </>
  );
}
