import React, { useEffect, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiRequest, UserService, SessionService } from '../lib/api';
import { useQuery } from '@tanstack/react-query';
import { 
  ShoppingBag, 
  ShoppingCart, 
  Package, 
  Sparkles, 
  User, 
  LayoutDashboard,
  MapPin,
  LogOut,
  Wifi,
  Radio
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";

// --- DESKTOP SIDEBAR ---
const DesktopSidebar = ({ user, signOut, cartCount, isAdmin, sessionInfo }) => {
  const location = useLocation();
  
  const navItems = [
    { title: "Shop", url: "/dash/shop", icon: ShoppingBag },
    { title: "Concierge", url: "/dash/agent", icon: Sparkles },
    { title: "My Bag", url: "/dash/cart", icon: ShoppingCart, badge: cartCount },
    { title: "Orders", url: "/dash/orders", icon: Package },
    { title: "Profile", url: "/dash/profile", icon: User },
  ];

  if (isAdmin) {
    navItems.push({ title: "Admin Panel", url: "/admin", icon: LayoutDashboard });
  }

  return (
    <aside className="hidden md:flex w-72 flex-col h-screen sticky top-0 border-r border-gray-100 bg-white z-50">
      <div className="p-8">
        <Link to="/" className="block">
          <h1 className="text-5xl font-serif font-bold text-black tracking-tighter hover:opacity-80 transition-opacity">
            Daksha
          </h1>
        </Link>
      </div>

      <nav className="flex-1 px-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname.startsWith(item.url);
          return (
            <Link 
              key={item.title} 
              to={item.url}
              className={`
                flex items-center gap-4 px-5 py-4 rounded-full transition-all duration-300 group relative
                ${isActive ? 'bg-black text-white shadow-xl shadow-black/5' : 'text-gray-400 hover:bg-gray-50 hover:text-black'}
              `}
            >
              <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              <span className="font-medium tracking-wide text-sm">{item.title}</span>
              {item.badge > 0 && (
                <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full ${isActive ? 'bg-white text-black' : 'bg-gray-100 text-black'}`}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Session Active Indicator */}
      {sessionInfo && (
        <div className="px-6 pb-4">
          <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3 flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
              <Radio size={16} className="animate-pulse" />
            </div>
            <div className="overflow-hidden">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-800">Active Session</p>
              <p className="text-[10px] text-emerald-600 truncate font-mono">{sessionInfo.session_id.slice(0,12)}...</p>
            </div>
          </div>
        </div>
      )}

      <div className="p-6 border-t border-gray-100">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-3 w-full p-2 rounded-xl hover:bg-gray-50 transition-colors text-left outline-none">
              <Avatar className="h-10 w-10 border border-gray-200">
                <AvatarFallback className="bg-gray-100 text-black font-serif">
                  {user?.email?.[0].toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-bold truncate text-gray-900">{user?.user_metadata?.full_name || 'Member'}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 p-2 rounded-xl border-gray-100 shadow-xl">
            <DropdownMenuItem onClick={signOut} className="text-red-500 focus:text-red-600 focus:bg-red-50 cursor-pointer rounded-lg p-2">
              <LogOut className="mr-2 h-4 w-4" /> Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
};

export default function UserLayout() {
    const location = useLocation();
    const { user, profile, signOut } = useAuth();
    const [userLocation, setUserLocation] = useState(null);
    const [sessionInfo, setSessionInfo] = useState(null);

    // --- 1. START SESSION & SYNC LOCATION ---
    useEffect(() => {
        const initUserSession = async () => {
            if (!user) return;

            try {
                // A. Start/Get Session
                let active = await SessionService.getActive();
                if (!active || !active.data) { // Check if data exists in response
                    const res = await SessionService.start('web');
                    active = res.data;
                } else {
                    active = active.data;
                }
                setSessionInfo(active);

                // B. Location Sync Logic
                if ("geolocation" in navigator) {
                    navigator.geolocation.getCurrentPosition(async (position) => {
                        const { latitude, longitude } = position.coords;
                        setUserLocation({ lat: latitude, lng: longitude });
                        
                        // Fetch addresses to find one to update
                        const addrRes = await UserService.getAddresses();
                        const addresses = addrRes.data || [];
                        
                        if (addresses.length > 0) {
                            // Prioritize default, otherwise first
                            const targetAddr = addresses.find(a => a.is_default) || addresses[0];
                            
                            // Call the PATCH endpoint
                            await UserService.updateAddressLocation(targetAddr.id, latitude, longitude);
                            console.log("📍 Location synced to backend for address:", targetAddr.id);
                        } else {
                            console.log("📍 Location captured but no address found to update.");
                        }
                    }, (err) => {
                        console.warn("Geolocation permission denied", err);
                    });
                }
            } catch (e) {
                console.error("Initialization failed", e);
            }
        };

        initUserSession();
    }, [user]);

    // --- 2. CART DATA ---
    const { data: cart } = useQuery({
        queryKey: ['cart'],
        queryFn: () => apiRequest('/user/cart'),
        refetchInterval: 5000, 
        enabled: !!user
    });
    
    const cartCount = cart?.items?.reduce((acc, item) => acc + item.quantity, 0) || 0;
    const isAdmin = profile?.role === 'admin' || user?.app_metadata?.role === 'admin';

    const mobileNavItems = [
        { title: 'Shop', url: '/dash/shop', icon: ShoppingBag },
        { title: 'Agent', url: '/dash/agent', icon: Sparkles },
        { title: 'Bag', url: '/dash/cart', icon: ShoppingCart, badge: cartCount },
        { title: 'Profile', url: '/dash/profile', icon: User },
    ];

    const isChatPage = location.pathname.includes('/agent');

    return (
        <div className="flex min-h-screen w-full bg-[#FDFDFD] font-sans text-zinc-900 selection:bg-black selection:text-white">
            
            <DesktopSidebar 
                user={user} 
                signOut={signOut} 
                cartCount={cartCount} 
                isAdmin={isAdmin} 
                sessionInfo={sessionInfo}
            />

            <div className="flex-1 flex flex-col min-h-screen relative">
                
                {/* Mobile Header */}
                <header className="md:hidden sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-100 px-6 py-4 flex justify-between items-center">
                    <Link to="/" className="text-3xl font-serif font-bold tracking-tighter">Daksha</Link>
                    {sessionInfo && (
                        <div className="flex items-center gap-1 text-[10px] uppercase tracking-widest text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                            <Wifi size={10} className="animate-pulse" /> Live
                        </div>
                    )}
                </header>

                {/* Page Content */}
                <main className={`flex-1 w-full max-w-7xl mx-auto p-4 md:p-10 ${isChatPage ? 'pb-20' : 'pb-32'} animate-in fade-in duration-500`}>
                    <Outlet />
                </main>

                {/* Mobile Nav */}
                <div className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-auto">
                    <motion.nav 
                        initial={{ y: 100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        className="flex items-center gap-2 bg-black/90 backdrop-blur-xl p-2 rounded-full shadow-2xl ring-1 ring-white/10"
                    >
                        {mobileNavItems.map((item) => {
                            const isActive = location.pathname.startsWith(item.url);
                            return (
                                <Link key={item.url} to={item.url} className="relative group">
                                    <div className={`
                                        w-12 h-12 flex items-center justify-center rounded-full transition-all duration-300
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
            </div>
        </div>
    );
}