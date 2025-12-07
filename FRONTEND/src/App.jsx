import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "@/pages/auth/Login";
import ProfileCompletion from "@/pages/auth/ProfileCompletion";
import Layout from "@/components/layout/Layout";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import Catalog from "@/pages/shop/Catalog";
import Cart from "@/pages/cart/Cart";
import Profile from "@/pages/account/Profile";
import { useAuth } from "./context/AuthContext";

function App() {
  const { token } = useAuth();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={token ? <Navigate to="/" /> : <Login />} />
        
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Catalog />} />
          <Route path="cart" element={<Cart />} />
          <Route path="profile" element={<Profile />} />
          <Route path="support" e lement={<div>Support Page</div>} />
          <Route path="orders" element={<div>Orders Page</div>} />
        </Route>

        <Route path="/complete-profile" element={
          <ProtectedRoute>
            <ProfileCompletion />
          </ProtectedRoute>
        } />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;