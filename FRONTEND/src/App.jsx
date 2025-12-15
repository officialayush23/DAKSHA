// src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { RegisterProfilePage } from "@/pages/RegisterProfile";
import Dashboard from "@/pages/Dashboard";
import OrdersPage from "@/pages/Order"; // Renamed import to match usage
import ProfilePage from "@/pages/Profile"
import CartPage from "@/pages/Cart"
import ProductPage from "@/pages/Products"
import SupportPage from "@/pages/Support"
import Payment from "@/pages/Payment"
import { GlobalLayout } from "./components/layout/GlobalLayout";
import Chat from "./pages/Chat";

function AppInner() {
  const { user, profile, logout } = useAuth();

  return (
    <>
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
      <Route path="/signup" element={user ? <Navigate to="/dashboard" replace /> : <SignupPage />} />
      
      {/* Root Redirect */}
      <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} replace />} />

      {/* --- Protected Routes (Wrapped in GlobalLayout for AI Button) --- */}
      <Route element={<GlobalLayout />}>
        
        {/* Registration is protected but usually standalone, but putting here is fine */}
        <Route path="/register" element={user ? <RegisterProfilePage /> : <Navigate to="/login" replace />} />
        
        {/* Main App Pages */}
        <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/login" replace />} />
        <Route path="/orders" element={user ? <OrdersPage /> : <Navigate to="/login" replace />} />
        
        {/* Placeholder Pages */}
        <Route path="/products" element={user ? <ProductPage /> : <Navigate to="/login" replace />} />
        <Route path="/cart" element={user ? <CartPage /> : <Navigate to="/login" replace />} />
        <Route path="/support" element={user ? <SupportPage /> : <Navigate to="/login" replace />} />
        <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/login" replace />} />
        <Route path="/payment" element={user ? <Payment /> : <Navigate to="/login" replace />} />
            <Route path="/chat" element={user ? <Chat/> : <Navigate to="/login" replace />} />
      </Route>
      </Routes>

      {/* {user && (
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
      )} */}
    </>
  );
}

export default function App() {
  return <AppInner />;
}
