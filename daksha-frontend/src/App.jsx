// src/App.jsx
import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from './context/AuthContext';

// --- LAYOUTS ---
import UserLayout from './layout/UserLayout'; // The new Dashboard Layout
import AdminLayout from './admin/AdminLayout';

// --- PUBLIC PAGES ---
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import ErrorPage from './pages/ErrorPage';

// --- DASHBOARD PAGES ---
import ShopPage from './pages/ShopPage';
import ProductDetail from './pages/ProductDetail';
import ProfilePage from './pages/ProfilePage';
import ChatInterface from './pages/ChatInterface';

// --- ADMIN PAGES ---
import AdminAuthPage from './pages/AuthPage';
import Dashboard from './admin/pages/Dashboard';
import Products from './admin/pages/Products';
import Stores from './admin/pages/Stores';
import Orders from './admin/pages/Orders';
import Complaints from './admin/pages/Complaints';
import Offers from './admin/pages/Offers';
import Handoffs from './admin/pages/Handoffs';
import Returns from './admin/pages/Returns';
import Kiosks from './admin/pages/Kiosk';

// --- KIOSK MODULE ---
import KioskRoutes from './kiosk/routes';
import OrdersPage from './pages/OrdersPage';
import CartPage from './pages/CartPage';
import DiscountRules from './admin/pages/DiscountRules';

// --- PROTECTED ROUTE WRAPPERS ---

// 1. Admin Guard (Checks Supabase Session)
const AdminProtectedRoute = ({ children }) => {
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

  if (loading) return <div className="flex h-screen items-center justify-center">Loading Admin...</div>;
  if (!session) return <Navigate to="/admin/login" state={{ from: location }} replace />;
  return children;
};

// 2. User Dashboard Guard (Uses AuthContext)
const UserProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="h-screen flex items-center justify-center bg-[#FDFDFD]">Loading Daksha...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

export default function App() {
  return (
    <Routes>
      {/* ============================== */}
      {/* 1. PUBLIC ROUTES               */}
      {/* ============================== */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<AuthPage />} />
      <Route path="/register" element={<AuthPage isRegister />} />

      {/* ============================== */}
      {/* 2. USER DASHBOARD (Protected)  */}
      {/* ============================== */}
      <Route path="/dash" element={<UserProtectedRoute><UserLayout /></UserProtectedRoute>}>
        <Route index element={<Navigate to="shop" replace />} />
        
        <Route path="shop" element={<ShopPage />} />
        <Route path="product/:id" element={<ProductDetail />} />
        <Route path="profile" element={<ProfilePage />} />
        
        {/* Agent/Chat Page */}
        <Route path="agent" element={
          <div className="h-full flex items-center justify-center">
             <div className="w-full max-w-4xl h-full">
               <ChatInterface />
             </div>
          </div>
        } />
        
        {/* Placeholders for now */}
        <Route path="orders" element={<OrdersPage/>} />
        <Route path="cart" element={<CartPage/>} />
        
        <Route path="*" element={<ErrorPage />} />
      </Route>

      {/* ============================== */}
      {/* 3. KIOSK MODULE                */}
      {/* ============================== */}
      <Route path="/kiosk/*" element={<KioskRoutes />} />

      {/* ============================== */}
      {/* 4. ADMIN PANEL                 */}
      {/* ============================== */}
      <Route path="/admin/login" element={<AdminAuthPage />} />
      
      <Route path="/admin" element={<AdminProtectedRoute><AdminLayout /></AdminProtectedRoute>}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="stores" element={<Stores />} />
        <Route path="orders" element={<Orders />} />
        <Route path="complaints" element={<Complaints />} />
        <Route path="offers" element={<Offers />} />
        <Route path="handoffs" element={<Handoffs />} />
        <Route path="returns" element={<Returns />} />
        <Route path="kiosks" element={<Kiosks />} />
        <Route path="discount-rules" element={<DiscountRules />} />
        <Route path="*" element={<Navigate to="dashboard" replace />} />
      </Route>



      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}