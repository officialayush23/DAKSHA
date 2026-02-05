// src/layouts/DashboardLayout.jsx
import React, { useEffect, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  ShoppingBag, Sparkles, User, LogOut, LayoutGrid, Package 
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Toaster } from 'sonner';

const NavItem = ({ to, icon: Icon, label, active }) => (
  <Link to={to} className={`
    flex items-center gap-4 px-6 py-4 rounded-xl transition-all duration-300 group
    ${active ? 'bg-black text-white shadow-xl' : 'text-gray-400 hover:bg-gray-100 hover:text-black'}
  `}>
    <Icon size={20} strokeWidth={active ? 2.5 : 2} />
    <span className="font-serif tracking-wide">{label}</span>
  </Link>
);

export default function DashboardLayout() {
  const { pathname } = useLocation();
  const { user, signOut } = useAuth();
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', checkMobile);
    checkMobile();
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const NAV_LINKS = [
    { to: "/shop", icon: ShoppingBag, label: "Collection" },
    { to: "/agent", icon: Sparkles, label: "Concierge" }, // AI Agent
    { to: "/orders", icon: Package, label: "Orders" },
    { to: "/profile", icon: User, label: "Profile" },
  ];

  return (
    <div className="min-h-screen bg-[#FDFDFD] text-black flex font-sans selection:bg-black selection:text-white">
      {/* DESKTOP SIDEBAR */}
      {!isMobile && (
        <aside className="w-72 border-r border-gray-100 h-screen sticky top-0 p-8 flex flex-col justify-between bg-white z-50">
          <div>
            <h1 className="text-4xl font-serif font-bold mb-12 tracking-tighter">DAKSHA</h1>
            <nav className="space-y-2">
              {NAV_LINKS.map(l => (
                <NavItem key={l.to} {...l} active={pathname.startsWith(l.to)} />
              ))}
            </nav>
          </div>
          
          <div className="border-t border-gray-100 pt-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center font-serif text-lg">
                {user?.email?.[0].toUpperCase()}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-bold truncate">{user?.user_metadata?.name || 'Member'}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button onClick={signOut} className="flex items-center gap-2 text-xs text-red-500 hover:underline uppercase tracking-widest">
              <LogOut size={14} /> Sign Out
            </button>
          </div>
        </aside>
      )}

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 relative">
        <Outlet />
      </main>

      {/* MOBILE DYNAMIC ISLAND */}
      {isMobile && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
          <motion.div 
            initial={{ y: 100 }} animate={{ y: 0 }}
            className="flex items-center gap-1 bg-black/90 backdrop-blur-xl p-2 rounded-full shadow-2xl ring-1 ring-white/20"
          >
            {NAV_LINKS.map((l) => (
              <Link key={l.to} to={l.to} className={`
                w-12 h-12 flex items-center justify-center rounded-full transition-all
                ${pathname.startsWith(l.to) ? 'bg-white text-black' : 'text-gray-400'}
              `}>
                <l.icon size={20} />
              </Link>
            ))}
          </motion.div>
        </div>
      )}
      
      <Toaster position="top-center" toastOptions={{ className: 'font-serif' }} />
    </div>
  );
}