import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from "@/components/ui/sonner"
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';

// Simple Route Guard
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('daksha_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <BrowserRouter>
      {/* 🔔 The Notification System */}
      <Toaster position="top-center" richColors />
      
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        
        {/* Protected Dashboard Route */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Default Redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;