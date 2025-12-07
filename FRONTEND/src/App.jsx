// src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { RegisterProfilePage } from "@/pages/RegisterProfile";

function AppInner() {
  const { user, profile, logout } = useAuth();

  return (
    <>
      <Routes>
        <Route
          path="/"
          element={<Navigate to={user ? "/register" : "/login"} replace />}
        />
        <Route
          path="/login"
          element={user ? <Navigate to="/register" replace /> : <LoginPage />}
        />
        <Route
          path="/signup"
          element={user ? <Navigate to="/register" replace /> : <SignupPage />}
        />
        <Route path="/register" element={<RegisterProfilePage />} />
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

export default function App() {
  return <AppInner />;
}
