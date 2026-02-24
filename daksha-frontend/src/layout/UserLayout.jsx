import React, { useEffect, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiRequest, UserService, SessionService, CartService } from '../lib/api';
import { useQuery } from '@tanstack/react-query';
import {
  ShoppingBag,
  ShoppingCart,
  Package,
  Sparkles,
  User,
  LayoutDashboard,
  LogOut,
  Wifi,
  Radio,
  Heart // <-- Imported Heart for Wishlist
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
    { title: "Wishlist", url: "/dash/wishlist", icon: Heart }, // <-- Added Wishlist
    { title: "My Bag", url: "/dash/cart", icon: ShoppingCart, badge: cartCount },
    { title: "Orders", url: "/dash/orders", icon: Package },
    { title: "Returns", url: "/dash/return", icon: User },
    { title: "Profile", url: "/dash/profile", icon: User },
  ];

  if (isAdmin) {
    navItems.push({ title: "Admin Panel", url: "/admin", icon: LayoutDashboard });
  }

  return (
    <aside className="hidden md:flex w-72 flex-col h-screen sticky top-0 border-r border-zinc-100 bg-white z-50 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
      <div className="p-8">
        <Link to="/" className="block">
          <h1 className="text-4xl font-serif font-bold text-zinc-900 tracking-tight hover:text-black transition-colors">
            Daksha.
          </h1>
        </Link>
      </div>

      <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname.startsWith(item.url);
          const isWishlist = item.title === "Wishlist";
          
          return (
            <Link
              key={item.title}
              to={item.url}
              className={`
                flex items-center gap-4 px-5 py-3.5 rounded-2xl transition-all duration-300 group relative
                ${isActive 
                  ? 'bg-zinc-900 text-white shadow-md' 
                  : 'text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900'}
              `}
            >
              <item.icon 
                size={20} 
                strokeWidth={isActive ? 2.5 : 2} 
                // Add a subtle red tint/fill ONLY for the wishlist icon when hovered or active
                className={`transition-all duration-300 group-hover:scale-110 
                  ${isWishlist && isActive ? 'fill-red-500 text-red-500' : ''}
                  ${isWishlist && !isActive ? 'group-hover:text-red-500' : ''}
                `} 
              />
              <span className="font-medium tracking-wide text-sm">{item.title}</span>
              {item.badge > 0 && (
                <span className={`ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full ${isActive ? 'bg-white text-black' : 'bg-zinc-200 text-zinc-700'}`}>
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
          <div className="bg-emerald-50/50 border border-emerald-100 rounded-2xl p-3 flex items-center gap-3">
            <div className="h-8 w-8 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600 shadow-sm">
              <Radio size={16} className="animate-pulse" />
            </div>
            <div className="overflow-hidden">
              <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-800">Active Session</p>
              <p className="text-[10px] text-emerald-600 truncate font-mono mt-0.5">{sessionInfo.session_id.slice(0, 12)}...</p>
            </div>
          </div>
        </div>
      )}

      <div className="p-6 border-t border-zinc-100">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-3 w-full p-2.5 rounded-2xl hover:bg-zinc-50 transition-colors text-left outline-none border border-transparent hover:border-zinc-200">
              <Avatar className="h-10 w-10 border border-zinc-200 shadow-sm">
                <AvatarFallback className="bg-zinc-100 text-zinc-900 font-serif font-bold">
                  {user?.email?.[0].toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-bold truncate text-zinc-900">{user?.user_metadata?.full_name || 'Member'}</p>
                <p className="text-xs text-zinc-400 truncate">{user?.email}</p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 p-2 rounded-2xl border-zinc-100 shadow-xl">
            <DropdownMenuItem onClick={signOut} className="text-red-600 focus:text-red-700 focus:bg-red-50 cursor-pointer rounded-xl p-3 font-medium">
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
        let active = await SessionService.getActive().catch(() => null);
        if (!active || !active.data) { 
          const res = await SessionService.start('web');
          active = res?.data || res;
        } else {
          active = active.data;
        }
        setSessionInfo(active);

        if ("geolocation" in navigator) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              const { latitude, longitude } = position.coords;
              setUserLocation({ lat: latitude, lng: longitude });

              await apiRequest("/user/ping", {
                method: "POST",
                params: { lat: latitude, lng: longitude }
              }).catch(() => {}); // silent fail for ping
            },
            (err) => console.warn("Geolocation denied", err),
            { enableHighAccuracy: true }
          );
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
    queryFn: () => CartService.get(),
    refetchInterval: 5000,
    enabled: !!user
  });

  const cartData = cart?.data || cart;
  const cartCount = cartData?.total_items || cartData?.items?.reduce((acc, item) => acc + item.quantity, 0) || 0;
  
  const isAdmin = profile?.role === 'admin' || user?.app_metadata?.role === 'admin';

  // --- MOBILE NAV (Added Wishlist) ---
  const mobileNavItems = [
    { title: 'Shop', url: '/dash/shop', icon: ShoppingBag },
    { title: 'Wishlist', url: '/dash/wishlist', icon: Heart }, // <-- Added Wishlist
    { title: 'Agent', url: '/dash/agent', icon: Sparkles },
    { title: 'Bag', url: '/dash/cart', icon: ShoppingCart, badge: cartCount },
    { title: 'Profile', url: '/dash/profile', icon: User },
  ];

  const isChatPage = location.pathname.includes('/agent');

  return (
    <div className="flex min-h-screen w-full bg-[#FCFCFC] font-sans text-zinc-900 selection:bg-black selection:text-white">

      <DesktopSidebar
        user={user}
        signOut={signOut}
        cartCount={cartCount}
        isAdmin={isAdmin}
        sessionInfo={sessionInfo}
      />

      <div className="flex-1 flex flex-col min-h-screen relative overflow-x-hidden">

        {/* Mobile Header */}
        <header className="md:hidden sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-zinc-100 px-6 py-4 flex justify-between items-center shadow-sm">
          <Link to="/" className="text-3xl font-serif font-bold tracking-tight">Daksha.</Link>
          {sessionInfo && (
            <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-widest text-emerald-700 bg-emerald-50 border border-emerald-100 px-3 py-1.5 rounded-full shadow-sm">
              <Wifi size={12} className="animate-pulse" /> Live
            </div>
          )}
        </header>

        {/* Page Content */}
        <main className={`flex-1 w-full max-w-[1600px] mx-auto p-4 md:p-6 lg:p-8 xl:p-10 ${isChatPage ? 'pb-20' : 'pb-32'} animate-in fade-in duration-500`}>
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
              const isWishlist = item.title === "Wishlist";
              
              return (
                <Link key={item.url} to={item.url} className="relative group">
                  <div className={`
                    w-12 h-12 flex items-center justify-center rounded-full transition-all duration-300
                    ${isActive ? 'bg-white text-black scale-110 shadow-lg' : 'text-zinc-400 hover:text-zinc-200'}
                  `}>
                    <item.icon 
                      size={20} 
                      strokeWidth={isActive ? 2.5 : 2} 
                      className={`
                        ${isWishlist && isActive ? 'fill-red-500 text-red-500' : ''}
                      `}
                    />
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