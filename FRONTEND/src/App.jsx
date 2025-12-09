// src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Loader2 } from "lucide-react";

// Layouts
import { GlobalLayout } from "@/components/layout/GlobalLayout";

// Pages
import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { RegisterProfilePage } from "@/pages/RegisterProfile";
import Dashboard from "@/pages/Dashboard";
import OrdersPage from "@/pages/Orders"; // Renamed import to match usage
import ProfilePage from "@/pages/Profile"
import CartPage from "@/pages/Cart"
import ProductPage from "@/pages/Products"
import SupportPage from "@/pages/Support"
import Payment from "@/pages/Payment"

// --- Placeholder Pages (Create real files for these later) ---

function AppInner() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <Routes>
      {/* --- Public Routes (No AI Button) --- */}
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
      </Route>
    </Routes>
  );
}

export default function App() {
  return <AppInner />;
}
