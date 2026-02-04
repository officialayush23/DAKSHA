import React, { useEffect, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { AppSidebar } from '../../components/app-sidebar';
import { useAuth } from '../../context/AuthContext';
import { apiRequest } from '../../lib/api';
import { useAnalytics } from '../../hooks/useAnalytics'; 
import { useQuery } from '@tanstack/react-query';
import { 
  ShoppingBag, 
  ShoppingCart, 
  Package, 
  Sparkles, 
  User, 
  LayoutDashboard,
  MapPin
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Shadcn Imports
import { 
  SidebarProvider, 
  SidebarInset, 
} from '../../components/ui/sidebar';

export default function DemoLayout() {
    const location = useLocation();
    const { user, profile } = useAuth();
    const [userLocation, setUserLocation] = useState(null);
    const { trackEvent } = useAnalytics(); 

    // --- Location Sync ---
    useEffect(() => {
        const updateLocation = () => {
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(async (position) => {
                    const { latitude, longitude } = position.coords;
                    setUserLocation({ lat: latitude, lng: longitude });
                    try {
                        await apiRequest(`/users/location?lat=${latitude}&lng=${longitude}`, { method: 'PATCH' });
                        console.log("Location synced");
                    } catch (e) {
                        console.error("Location sync failed", e);
                    }
                }, (err) => {
                    console.warn("Geolocation permission denied", err);
                });
            }
        };
        updateLocation();
        const interval = setInterval(updateLocation, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    // --- Nav Data ---
    const { data: cart } = useQuery({
        queryKey: ['cart'],
        queryFn: () => apiRequest('/cart/'),
        refetchInterval: 5000, 
    });
    const cartCount = cart?.items?.reduce((acc, item) => acc + item.quantity, 0) || 0;
    const isAdmin = profile?.role === 'admin' || user?.app_metadata?.role === 'admin';

    const mobileNavItems = [
        { name: 'Shop', path: '/demo/products', icon: ShoppingBag },
        { name: 'Agent', path: '/demo/chat', icon: Sparkles },
        { name: 'Cart', path: '/demo/cart', icon: ShoppingCart, badge: cartCount },
        { name: 'Orders', path: '/demo/orders', icon: Package },
        { name: 'Profile', path: '/demo/profile', icon: User },
    ];
    if(isAdmin) mobileNavItems.push({ name: 'Admin', path: '/demo/admin', icon: LayoutDashboard });

    // Move Island to top if on Chat page
    const isChatPage = location.pathname.includes('/chat');

    return (
        <SidebarProvider>
            <div className="flex min-h-screen w-full bg-white font-sans text-zinc-900">
                
                {/* --- DESKTOP SIDEBAR --- */}
                <AppSidebar />

                <SidebarInset className="bg-white min-h-screen flex flex-col">
                    {/* --- MOBILE BRANDING HEADER --- */}
                    <div className="md:hidden pt-8 px-6 pb-2 bg-white/80 backdrop-blur-xl sticky top-0 z-40 flex justify-between items-end">
                        <h1 className="text-4xl font-charm font-bold text-black">Weeb</h1>
                        {userLocation && (
                            <div className="flex items-center gap-1 text-[10px] text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full font-medium">
                                <MapPin size={10} /> Local
                            </div>
                        )}
                    </div>

                    {/* --- MAIN CONTENT --- */}
                    <main className="flex-1 p-6 md:p-12 max-w-7xl mx-auto w-full pb-32 md:pb-12 animate-in fade-in duration-500">
                        <Outlet />
                    </main>

                    {/* --- DYNAMIC ISLAND (MOBILE) --- */}
                    <div className={`md:hidden fixed left-1/2 -translate-x-1/2 z-50 w-auto transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] ${isChatPage ? 'top-6' : 'bottom-8'}`}>
                        <motion.nav 
                            layout
                            className="flex items-center gap-1 bg-black/90 backdrop-blur-xl p-2 rounded-full shadow-2xl shadow-black/20 ring-1 ring-white/10"
                        >
                            {mobileNavItems.map((item) => {
                                const isActive = location.pathname.startsWith(item.path);
                                return (
                                    <Link key={item.path} to={item.path} className="relative">
                                        <div className={`
                                            relative w-12 h-12 flex items-center justify-center rounded-full transition-all duration-300
                                            ${isActive ? 'bg-white text-black scale-110 shadow-lg' : 'text-zinc-400 hover:text-zinc-200'}
                                        `}>
                                            <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                                            {item.badge > 0 && (
                                                <span className={`
                                                    absolute top-2 right-2 w-2.5 h-2.5 rounded-full border-2 border-black
                                                    ${isActive ? 'bg-black border-white' : 'bg-white'}
                                                `} />
                                            )}
                                        </div>
                                    </Link>
                                );
                            })}
                        </motion.nav>
                    </div>

                </SidebarInset>
            </div>
        </SidebarProvider>
    );
}