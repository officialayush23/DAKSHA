// src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { RegisterProfilePage } from "@/pages/RegisterProfile";

import HomePage from "@/pages/HomePage";
import OrdersPage from "@/pages/Order";
import ProfilePage from "@/pages/Profile";
import CartPage from "@/pages/Cart";
import ProductPage from "@/pages/Products";
import SupportPage from "@/pages/Support";
import Payment from "@/pages/Payment";
import Chat from "@/pages/Chat";

import { GlobalLayout } from "@/components/layout/GlobalLayout";

function AppInner() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={user ? <Navigate to="/home" replace /> : <LoginPage />} />
      <Route path="/signup" element={user ? <Navigate to="/home" replace /> : <SignupPage />} />

      {/* Root */}
      <Route path="/" element={<Navigate to={user ? "/home" : "/login"} replace />} />

      {/* Protected */}
      <Route element={<GlobalLayout />}>
        <Route path="/register" element={user ? <RegisterProfilePage /> : <Navigate to="/login" replace />} />

        <Route path="/home" element={user ? <HomePage /> : <Navigate to="/login" replace />} />
        <Route path="/orders" element={user ? <OrdersPage /> : <Navigate to="/login" replace />} />
        <Route path="/products" element={user ? <ProductPage /> : <Navigate to="/login" replace />} />
        <Route path="/cart" element={user ? <CartPage /> : <Navigate to="/login" replace />} />
        <Route path="/support" element={user ? <SupportPage /> : <Navigate to="/login" replace />} />
        <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/login" replace />} />
        <Route path="/payment" element={user ? <Payment /> : <Navigate to="/login" replace />} />
        <Route path="/chat" element={user ? <Chat /> : <Navigate to="/login" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return <AppInner />;
}
