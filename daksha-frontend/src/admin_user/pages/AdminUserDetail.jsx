import React, { useEffect, useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  User, ShoppingBag, ShoppingCart, Activity, 
  Award, Ticket, Bot, AlertOctagon, Star, 
  Mail, Phone, Calendar, Shield, ChevronRight,
  ArrowLeft
} from 'lucide-react';

// --- SERVICE ---
import { AdminUserService } from '@/lib/adminUserService'; 

// --- UI COMPONENTS ---
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

// --- SUB-COMPONENTS ---
import UserProfile from '../components/UserProfile';
import UserOrders from '../components/UserOrders';
import UserCarts from '../components/UserCarts';
import UserSessions from '../components/UserSessions';
import UserLoyalty from '../components/UserLoyalty';
import UserCoupons from '../components/UserCoupons';
import UserAgentData from '../components/UserAgentData';
import UserComplaints from '../components/UserComplaints';
import UserReviews from '../components/UserReviews';

const TABS = [
  { id: 'profile', label: 'Account Profile', icon: User },
  { id: 'orders', label: 'Order History', icon: ShoppingBag },
  { id: 'carts', label: 'Carts', icon: ShoppingCart },
  { id: 'sessions', label: 'Sessions', icon: Activity },
  { id: 'loyalty', label: 'Loyalty', icon: Award },
  { id: 'coupons', label: 'Coupons', icon: Ticket },
  { id: 'agent', label: 'AI Agent', icon: Bot },
  { id: 'complaints', label: 'Complaints', icon: AlertOctagon },
  { id: 'reviews', label: 'Reviews', icon: Star },
];

export default function AdminUserDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile');
  
  // Ref to prevent duplicate fetches if React StrictMode double-invokes
  const isFetching = useRef(false);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      if (!id || isFetching.current) return;
      
      try {
        isFetching.current = true;
        setLoading(true);
        const res = await AdminUserService.getUserProfile(id);
        
        if (isMounted) {
          const profileData = res?.data || res;
          setUser(profileData);
        }
      } catch (err) {
        if (isMounted) {
          toast.error("Failed to load user profile");
          navigate('/admin/users');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
          isFetching.current = false;
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
      isFetching.current = false;
    };
  }, [id]); // Only re-run when ID changes

  // Memoize content to prevent unnecessary re-renders of heavy lists
  const tabContent = useMemo(() => {
    if (!user) return null;
    const components = {
      profile: <UserProfile userId={id} user={user} />,
      orders: <UserOrders userId={id} />,
      carts: <UserCarts userId={id} />,
      sessions: <UserSessions userId={id} />,
      loyalty: <UserLoyalty userId={id} />,
      coupons: <UserCoupons userId={id} />,
      agent: <UserAgentData userId={id} />,
      complaints: <UserComplaints userId={id} />,
      reviews: <UserReviews userId={id} />,
    };
    return components[activeTab] || components.profile;
  }, [activeTab, id, user]);

  if (loading) {
    return (
      <div className="p-8 space-y-8">
        <Skeleton className="h-48 w-full rounded-[2.5rem] bg-zinc-100" />
        <div className="flex gap-8">
          <Skeleton className="h-[500px] w-80 shrink-0 rounded-[2.5rem] bg-zinc-50" />
          <Skeleton className="h-[600px] flex-1 rounded-[2.5rem] bg-zinc-50" />
        </div>
      </div>
    );
  }

  if (!user) return null;

  const initials = (user.name || user.email || "U").charAt(0).toUpperCase();

  return (
    <div key={id} className="p-4 md:p-8 space-y-8 max-w-[1600px] mx-auto pb-20">
      
      {/* 1. TOP NAV */}
      <button 
        onClick={() => navigate('/admin/users')}
        className="flex items-center gap-2 text-zinc-400 hover:text-zinc-900 font-bold text-xs uppercase tracking-[0.2em] transition-all group"
      >
        <ArrowLeft size={14} className="group-hover:-translate-x-1 transition-transform" />
        User Directory
      </button>

      {/* 2. HEADER CARD */}
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-sm p-8 md:p-10 flex flex-col md:flex-row items-center gap-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-zinc-50 rounded-full blur-3xl opacity-50 -translate-y-1/2 translate-x-1/2 pointer-events-none" />
        
        <Avatar className="h-28 w-28 md:h-32 md:w-32 border-4 border-white shadow-xl ring-1 ring-zinc-100">
          <AvatarFallback className="bg-zinc-900 text-white font-serif font-bold text-4xl">
            {initials}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 text-center md:text-left relative z-10">
          <h1 className="text-3xl md:text-5xl font-serif font-bold text-zinc-900 mb-2 leading-tight">
            {user.name || "Customer Profile"}
          </h1>
          <div className="flex flex-wrap justify-center md:justify-start items-center gap-4 text-sm font-medium text-zinc-500">
            <span className="flex items-center gap-1.5"><Mail size={14} /> {user.email}</span>
            {user.phone && <span className="flex items-center gap-1.5"><Phone size={14} /> {user.phone}</span>}
          </div>
        </div>

        <div className="flex flex-col items-center md:items-end gap-3 shrink-0">
          <Badge className="bg-zinc-900 text-white px-4 py-1.5 text-[10px] tracking-widest uppercase border-none shadow-lg shadow-zinc-200">
            {user.role || 'customer'}
          </Badge>
          <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
            ID: {id.slice(-8).toUpperCase()}
          </span>
        </div>
      </div>

      {/* 3. SPLIT CONTENT */}
      <div className="flex flex-col lg:flex-row gap-8 items-start">
        
        {/* SIDEBAR */}
        <aside className="w-full lg:w-80 shrink-0 bg-white rounded-[2.5rem] p-5 border border-zinc-100 shadow-sm sticky top-24 z-10 hidden lg:block">
          <nav className="space-y-1">
            {TABS.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    w-full flex items-center justify-between px-5 py-4 rounded-2xl font-bold text-sm transition-all duration-300 group
                    ${isActive 
                      ? "bg-zinc-900 text-white shadow-xl shadow-zinc-200" 
                      : "text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900"}
                  `}
                >
                  <div className="flex items-center gap-4">
                    <tab.icon size={18} className={isActive ? "text-white" : "text-zinc-400 group-hover:text-zinc-900"} />
                    {tab.label}
                  </div>
                  {isActive && <ChevronRight size={16} className="opacity-40" />}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* MOBILE TABS */}
        <div className="lg:hidden w-full flex gap-2 overflow-x-auto pb-2 no-scrollbar">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-full font-bold text-xs uppercase tracking-widest whitespace-nowrap shrink-0 border transition-all
                ${activeTab === tab.id ? "bg-zinc-900 text-white border-zinc-900 shadow-lg" : "bg-white text-zinc-500 border-zinc-100"}
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* MAIN DISPLAY */}
        <main className="flex-1 w-full min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
            >
              {tabContent}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}