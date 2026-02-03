import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layout/MainLayout';
import LandingPage from './pages/LandingPage';
import ShopPage from './pages/ShopPage';
import ProductDetail from './pages/ProductDetail';
import AuthPage from './pages/AuthPage';
import ErrorPage from './pages/ErrorPage';

export default function App() {
  return (

      <Routes>
        <Route index element={<LandingPage />} />
        {/* MainLayout wraps all these routes */}
        <Route path="/" element={<MainLayout />}>
          
          <Route path="shop" element={<ShopPage />} />
          <Route path="product/:id" element={<ProductDetail />} />
          <Route path="login" element={<AuthPage />} />
          <Route path="register" element={<AuthPage isRegister={true} />} />
          
          {/* Catch-all for 404s */}
          <Route path="*" element={<ErrorPage />} />
        </Route>
      </Routes>

  );
}