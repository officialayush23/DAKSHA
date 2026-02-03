import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom'; // Changed hook
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PageLoader from '../components/ui/PageLoader';
import { Toaster } from 'sonner';

export default function MainLayout() {
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);

  // Trigger Loader on Route Change
  useEffect(() => {
    setIsLoading(true);
    // Fake loading delay to show the animation (since we don't have real data loaders anymore)
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1500); // 1.5s loader

    return () => clearTimeout(timer);
  }, [location.pathname]); // Run whenever path changes

  return (
    <>
      <Toaster position="bottom-right" theme="dark" />
      
      {/* The Loader handles its own exit animation via the prop */}
      <PageLoader isLoading={isLoading} />
      
      <Navbar />
      
      {/* Add a fade-in effect for the page content */}
      <div className={`min-h-screen pt-20 transition-opacity duration-500 ${isLoading ? 'opacity-0' : 'opacity-100'}`}>
        <Outlet />
      </div>
      
      <Footer />
    </>
  );
}