import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { supabase } from '@/lib/supabaseClient';

// Main Layouts & Pages (Public)
import MainLayout from './layout/MainLayout';
import LandingPage from './pages/LandingPage';
import ShopPage from './pages/ShopPage';
import ProductDetail from './pages/ProductDetail';
import AuthPage from './pages/AuthPage';
import ErrorPage from './pages/ErrorPage';

// Admin Layouts & Pages
import AdminLayout from './admin/AdminLayout';
import AdminAuthPage from './admin/pages/AuthPage';
import Dashboard from './admin/pages/Dashboard';
import Products from './admin/pages/Products';
import Stores from './admin/pages/Stores';
import Orders from './admin/pages/Orders';
import Complaints from './admin/pages/Complaints';
import Offers from './admin/pages/Offers';
import Handoffs from './admin/pages/Handoffs';
import Returns from './admin/pages/Returns';

// --- KIOSK MODULE ---
import KioskRoutes from './kiosk/routes';

// Protected Route Component for Admin
const ProtectedRoute = ({ children }) => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) return <div className="flex h-screen items-center justify-center">Loading...</div>;

  if (!session) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  return children;
};

export default function App() {
  return (
    <Routes>
      
      {/* --- KIOSK ROUTES (Standalone Module) --- */}
      {/* This mounts the Kiosk app at /kiosk/* */}
      <Route path="/kiosk/*" element={<KioskRoutes />} />


      {/* --- ADMIN AUTH --- */}
      <Route path="/admin/login" element={<AdminAuthPage />} />

      {/* --- ADMIN ROUTES (Protected) --- */}
      <Route path="/admin" element={
        <ProtectedRoute>
          <AdminLayout />
        </ProtectedRoute>
      }>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="stores" element={<Stores />} />
        <Route path="orders" element={<Orders />} />
        <Route path="complaints" element={<Complaints />} />
        <Route path="offers" element={<Offers />} />
        <Route path="handoffs" element={<Handoffs />} />
        <Route path="returns" element={<Returns />} />
        <Route path="*" element={<Navigate to="dashboard" replace />} />
      </Route>


      {/* --- PUBLIC WEB STORE ROUTES --- */}
      <Route path="/" element={<MainLayout />}>
        <Route index element={<LandingPage />} />
        <Route path="shop" element={<ShopPage />} />
        <Route path="product/:id" element={<ProductDetail />} />
        <Route path="login" element={<AuthPage />} />
        <Route path="register" element={<AuthPage isRegister={true} />} />
        <Route path="*" element={<ErrorPage />} />
      </Route>

      {/* Root redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
