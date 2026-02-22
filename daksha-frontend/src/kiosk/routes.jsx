// import React from 'react';
// import { Routes, Route, Navigate } from 'react-router-dom';
// import { KioskProvider } from './context/KioskSessionContext';
// import KioskSelectScreen from './pages/KioskSelectScreen';
// import KioskLayout from './layout/KioskLayout';

// // Pages
// import AttractScreen from './pages/AttractScreen';
// import LoginScreen from './pages/LoginScreen';
// import Catalog from './pages/Catalog';
// import ProductDetail from './pages/ProductDetail';
// import Checkout from './pages/Checkout';

// export default function KioskRoutes() {
//   return (
//     <KioskProvider>
//       <Routes>
//         {/* Attract Screen is outside layout (no header) */}
//         <Route index element={<AttractScreen />} />
//         <Route path="select" element={<KioskSelectScreen />} />
//         {/* Layout wraps shopping pages */}
//         <Route element={<KioskLayout />}>
//           <Route path="login" element={<LoginScreen />} />
//           <Route path="catalog" element={<Catalog />} />
//           <Route path="product/:id" element={<ProductDetail />} />
//           <Route path="checkout" element={<Checkout />} />
//         </Route>

//         {/* Fallback */}
//         <Route path="*" element={<Navigate to="/kiosk" replace />} />
//       </Routes>
//     </KioskProvider>
//   );
// }