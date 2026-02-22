// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext.jsx'
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { KioskProvider } from './kiosk/context/KioskSessionContext';

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
        </KioskProvider>
      </AuthProvider>
    </BrowserRouter>
  </QueryClientProvider>
)