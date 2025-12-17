// src/App.jsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import { RegisterProfilePage } from "@/pages/RegisterProfile";
import RoleProtectedRoute from "@/components/auth/RoleProtectedRoute";
import HomePage from "@/pages/HomePage";
import OrdersPage from "@/pages/Order";
import ProfilePage from "@/pages/Profile";
import CartPage from "@/pages/Cart";
import ProductPage from "@/pages/Products";
import ProductDetailPage from "@/pages/ProductDetail";
import SupportPage from "@/pages/Support";
import Payment from "@/pages/Payment";
import Chat from "@/pages/Chat";

// --- STORE MANAGER PAGES (NEW) ---
import StoreLayout from "@/modules/store_manager/StoreLayout";
import StoreManagerDashboard from "@/modules/store_manager/pages/StoreDashboard";
import InventoryInward from "@/modules/store_manager/pages/InventoryInward";
import OrderQueue from "@/modules/store_manager/pages/OrderQueue";
import InventoryList from "@/modules/store_manager/pages/InventoryList";
import HistoryLogs from "@/modules/store_manager/pages/HistoryLog";

// // --- INVENTORY / WAREHOUSE PAGES ---
// import InventoryLayout from "@/inventory/InventoryLayout";
// import WarehouseDashboard from "@/inventory/pages/StoreDashboard"; // Reusing or specific page
// import StockControl from "@/inventory/pages/StockControl";
// import OrderFulfillment from "@/inventory/pages/OrderFulfillment";

// --- CATALOG ADMIN PAGES ---
import CatalogLayout from "@/modules/catalog_admin/CatalogLayout";
import CatalogDashboard from "@/modules/catalog_admin/pages/Dashboard";
import ProductList from "@/modules/catalog_admin/pages/ProductList";
import CreateProduct from "@/modules/catalog_admin/pages/CreateProduct";
import CreateVariant from "@/modules/catalog_admin/pages/CreateVariant";
import CategoryManager from "@/modules/catalog_admin/pages/CategoryManager";

// --- SUPER ADMIN PAGES ---
import SuperAdminLayout from "@/modules/super_admin/SuperAdminLayout";
import CreateLocation from "@/modules/super_admin/pages/CreateLocation";
import AccessControl from "@/modules/super_admin/pages/AccessControl";

// --- WAREHOUSE MANAGER (Fulfillment) ---
import WarehouseLayout from "@/modules/warehouse_manager/WarehouseLayout";
import WarehouseDashboard from "@/modules/warehouse_manager/pages/Dashboard";
import WarehouseInventory from "@/modules/warehouse_manager/pages/Inventory";
import Inbound from "@/modules/warehouse_manager/pages/Inbound";
import Outbound from "@/modules/warehouse_manager/pages/OutboundOrders";

// -- SUPPORT AGENTS --
import SupportDashboard from "@/modules/support_agent/pages/Dashboard"
import SupportHistory from "@/modules/support_agent/pages/History"
import SupportTicketList from "@/modules/support_agent/pages/TicketList"
import SupportLayout from "@/modules/support_agent/SupportLayout"

// --- FULFILLMENT AGENT MODULE ---
import FulfillmentLayout from "./modules/fulfillment_agent/FulfillmentLayout";
import FulfillmentQueue from "./modules/fulfillment_agent/pages/Queue";
import FulfillmentHistory from "./modules/fulfillment_agent/pages/History";

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
        <Route path="/products/:id" element={user ? <ProductDetailPage /> : <Navigate to="/login" replace />} />
        <Route path="/cart" element={user ? <CartPage /> : <Navigate to="/login" replace />} />
        <Route path="/support" element={user ? <SupportPage /> : <Navigate to="/login" replace />} />
        <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/login" replace />} />
        <Route path="/payment" element={user ? <Payment /> : <Navigate to="/login" replace />} />
        <Route path="/chat" element={user ? <Chat /> : <Navigate to="/login" replace />} />



      </Route>

       {/* --- 🛡️ ROLE PROTECTED ROUTES (ADMIN PORTALS) --- */}
        
        {/* 1. STORE MANAGER PORTAL */}
        <Route element={<RoleProtectedRoute allowedRoles={['store_manager', 'super_admin']} />}>
          <Route path="/store-manager" element={<StoreLayout />}>
            <Route index element={<StoreManagerDashboard />} />
            <Route path="inward" element={<InventoryInward />} />
            <Route path="orders" element={<OrderQueue />} />
            <Route path="list" element={<InventoryList />} />
            <Route path="history" element={<HistoryLogs />} />
          </Route>
        </Route>

        <Route element={<RoleProtectedRoute allowedRoles={['warehouse_manager', 'super_admin']} />}>
          <Route path="/warehouse-manager" element={<WarehouseLayout />}>
            <Route index element={<WarehouseDashboard />} />
            <Route path="inventory" element={<WarehouseInventory />} />
            <Route path="inbound" element={<Inbound />} />
            <Route path="Outbound" element={<Outbound />} />
          </Route>
        </Route>

        {/* 2. WAREHOUSE / INVENTORY PORTAL
        <Route element={<RoleProtectedRoute allowedRoles={['warehouse_manager', 'super_admin']} />}>
          <Route path="/inventory" element={<InventoryLayout />}>
            <Route index element={<WarehouseDashboard />} />
            <Route path="stock" element={<StockControl />} />
            <Route path="orders" element={<OrderFulfillment />} />
          </Route>
        </Route> */}

        {/* 3. CATALOG ADMIN PORTAL */}
        <Route element={<RoleProtectedRoute allowedRoles={['catalog_admin', 'super_admin']} />}>
          <Route path="/catalog" element={<CatalogLayout />}>
            <Route index element={<CatalogDashboard />} />
            <Route path="list" element={<ProductList />} />
            <Route path="search" element={<ProductList />} />
            <Route path="create-product" element={<CreateProduct />} />
            <Route path="create-variant" element={<CreateVariant />} />
            <Route path="categories" element={<CategoryManager />} />
          </Route>
        </Route>

        {/* 4. SUPER ADMIN PORTAL */}
        <Route element={<RoleProtectedRoute allowedRoles={['super_admin']} />}>
          <Route path="/super-admin" element={<SuperAdminLayout />}>
            <Route path="" element={<CreateLocation />} />
            <Route path="rbac" element={<AccessControl />} />
          </Route>
        </Route>

        {/* 5. SUPPORT AGENT PORTAL */}
        <Route element={<RoleProtectedRoute allowedRoles={['support_agent' , 'super_admin']} />}>
          <Route path="support-agent" element={<SupportLayout />}>
          <Route index element={<SupportDashboard />} />
            <Route path="tickets" element={< SupportTicketList/>} />
            <Route path="history" element={<SupportHistory />} />
          </Route>
        </Route>

        {/* 6. FULFILLMENT AGENT PORTAL */}
        <Route path="/fulfillment-agent" element={<FulfillmentLayout />}>
          <Route index element={<FulfillmentQueue />} />
          <Route path="history" element={<FulfillmentHistory />} />
        </Route>

        {/* --- 404 FALLBACK --- */}
        <Route path="*" element={
          <div className="flex h-screen flex-col items-center justify-center text-zinc-400">
            <h1 className="text-4xl font-bold text-red-600 mb-2">404</h1>
            <p>Page Not Found</p>
            <Button variant="link" onClick={() => window.location.href = "/"}>Go Home</Button>
          </div>
        } />
    </Routes>
  );
}

export default function App() {
  return <AppInner />;
}
