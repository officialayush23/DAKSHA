// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext.jsx'
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { KioskProvider } from './kiosk/context/KioskSessionContext';
import { Toaster } from 'sonner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>                {/* ← BrowserRouter is outermost */}
      <AuthProvider>
        <KioskProvider>            {/* ← inside BrowserRouter so useNavigate works */}
          <App />                  {/* ← only ONE <App /> */}
          {/* one toast container for the whole app (shop, chat, cart, kiosk, admin, auth) */}
          <Toaster position="top-center" richColors closeButton duration={3500}
            toastOptions={{ className: 'font-sans' }} />
        </KioskProvider>
      </AuthProvider>
    </BrowserRouter>
  </QueryClientProvider>
)
// PWA: offline shell + installable app (production builds only)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => { /* non-fatal */ });
  });
}
