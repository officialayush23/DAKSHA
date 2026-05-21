import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { supabase } from '@/lib/supabaseClient';
import { useAuth } from './context/AuthContext';
import { useKiosk } from './kiosk/context/KioskSessionContext';

// --- LAYOUTS ---
import UserLayout from './layout/UserLayout';
import AdminLayout from './admin/AdminLayout';
import KioskLayout from './kiosk/layout/KioskLayout';

// --- PUBLIC PAGES ---
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import ErrorPage from './pages/ErrorPage';

// --- SHARED USER + KIOSK PAGES ---
import ShopPage from './pages/ShopPage';
import ProductDetail from './pages/ProductDetail';
import ProfilePage from './pages/ProfilePage';
import ChatInterface from './pages/ChatInterface';
import OrdersPage from './pages/OrdersPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';

// --- KIOSK-ONLY PAGES ---
import AttractScreen from './kiosk/pages/AttractScreen';
import LoginScreen from './kiosk/pages/LoginScreen';
import KioskSelectScreen from './kiosk/pages/KioskSelectScreen';
import WishlistPage from './pages/WishlistPage';

// --- ADMIN PAGES ---
import Dashboard from './admin/pages/Dashboard';
import Products from './admin/pages/Products';
import Stores from './admin/pages/Stores';
import Orders from './admin/pages/Orders';
import Complaints from './admin/pages/Complaints';
import Offers from './admin/pages/Offers';
import Handoffs from './admin/pages/Handoffs';
import Returns from './admin/pages/Returns';
import Kiosks from './admin/pages/Kiosk';
import DiscountRules from './admin/pages/DiscountRules';
import AgentRuns from './admin/pages/AgentRuns';
import Paymentmanage from './admin/pages/Paymentmanage';

// --- ADMIN USER CRM MODULE ---
import AdminUserLayout from './admin_user/AdminUserLayout';
import AdminUserList from './admin_user/pages/AdminUserList';
import AdminUserDetail from './admin_user/pages/AdminUserDetail';

import ReturnsPage from './pages/ReturnsPage';
import AdvancedArchitectureSimulator from './pages/Anim';


// ============================================================
// ROUTE GUARDS
// ============================================================

// 1. Admin Guard (Supabase session)
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

// 2. User Dashboard Guard (AuthContext)
const UserProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="h-screen flex items-center justify-center bg-[#FDFDFD]">Loading Daksha...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

// 3. Kiosk Guard — checks sessionActive from KioskSessionContext
const KioskProtectedRoute = ({ children }) => {
  const { sessionActive } = useKiosk();
  if (!sessionActive) return <Navigate to="/kiosk/login" replace />;
  return children;
};


// ============================================================
// APP
// ============================================================

export default function App() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.18, ease: "easeInOut" }}
        style={{ width: '100%' }}
      >
    <Routes location={location}>

      {/* ============================== */}
      {/* 1. PUBLIC ROUTES               */}
      {/* ============================== */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<AuthPage />} />
      <Route path="/register" element={<AuthPage isRegister />} />
      <Route path="/animation" element={<AdvancedArchitectureSimulator />} />



      {/* ============================== */}
      {/* 2. USER DASHBOARD (Protected)  */}
      {/* ============================== */}
      <Route
        path="/dash"
        element={
          <UserProtectedRoute>
            <UserLayout />
          </UserProtectedRoute>
        }
      >
        <Route index element={<Navigate to="shop" replace />} />
        <Route path="shop" element={<ShopPage />} />
        <Route path="product/:id" element={<ProductDetail />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
        <Route path="wishlist" element={<WishlistPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
        <Route path="return" element={<ReturnsPage/>} />
        <Route path="agent" element={
          <div className="h-full flex items-center justify-center">
            <div className="w-full max-w-4xl h-full">
              <ChatInterface />
            </div>
          </div>
        } />
        <Route path="*" element={<ErrorPage />} />
      </Route>


      {/* ============================== */}
      {/* 3. KIOSK MODULE                */}
      {/* ============================== */}
      <Route path="/kiosk">

        {/* Public kiosk screens — no session required */}
        <Route index element={<AttractScreen />} />
        <Route path="select" element={<KioskSelectScreen />} />
        <Route path="login" element={<LoginScreen />} />

        {/* Protected kiosk screens — reuses user pages inside KioskLayout */}
        <Route
          element={
            <KioskProtectedRoute>
              <KioskLayout />
            </KioskProtectedRoute>
          }
        >
          <Route path="shop" element={<ShopPage />} />
          <Route path="product/:id" element={<ProductDetail />} />
          <Route path="cart" element={<CartPage />} />
          <Route path="checkout" element={<CheckoutPage />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="chat" element={<ChatInterface />} />
          <Route path="*" element={<ErrorPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/kiosk" replace />} />
      </Route>


      {/* ============================== */}
      {/* 4. ADMIN PANEL                 */}
      {/* ============================== */}
      <Route path="/admin/login" element={<AuthPage />} />
      <Route
        path="/admin"
        element={
          <AdminProtectedRoute>
            <AdminLayout />
          </AdminProtectedRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="stores" element={<Stores />} />
        <Route path="orders" element={<Orders />} />
        <Route path="complaints" element={<Complaints />} />
        <Route path="agent-runs" element={<AgentRuns />} />
        <Route path="offers" element={<Offers />} />
        <Route path="handoffs" element={<Handoffs />} />
        <Route path="returns" element={<Returns />} />
        <Route path="kiosks" element={<Kiosks />} />
        <Route path="discount-rules" element={<DiscountRules />} />
        <Route path="payment-manage" element={<Paymentmanage />} />

        {/* ADMIN USER CRM MODULE */}
        <Route path="users" element={<AdminUserLayout />}>
          <Route index element={<AdminUserList />} />
          <Route path=":id" element={<AdminUserDetail />} />
        </Route>

        {/* Catch-all MUST be last */}
        <Route path="*" element={<Navigate to="dashboard" replace />} />
      </Route>


      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />

    </Routes>
      </motion.div>
    </AnimatePresence>
  );
}