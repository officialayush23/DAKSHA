import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Hash, User as UserIcon, Calendar, 
  CreditCard, TrendingUp, ShoppingBag 
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

export default function UserProfile({ userId, user }) {
  const [spend, setSpend] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSpendData = async () => {
      try {
        setLoading(true);
        const res = await AdminUserService.getUserSpend(userId);
        const spendData = res?.data || res;
        setSpend(spendData);
      } catch (error) {
        console.warn("Could not load spend data, defaulting to 0", error);
        // Fallback if the user has no orders or the API is still being built
        setSpend({ total_spend: 0, order_count: 0, aov: 0 }); 
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchSpendData();
  }, [userId]);

  if (!user) return null;

  // Formatting helpers
  const createdDate = new Date(user.created_at).toLocaleString('en-US', { 
    month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' 
  });
  
  // Safely extract spend metrics (adjusting to common API response structures)
  const totalSpend = spend?.total_spent || spend?.total_spend || 0;
  const orderCount = spend?.order_count || spend?.total_orders || 0;
  const aov = spend?.aov || spend?.average_order_value || (orderCount > 0 ? (totalSpend / orderCount).toFixed(2) : 0);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      
      {/* --- ACCOUNT DETAILS CARD --- */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-white rounded-[2.5rem] p-8 md:p-10 border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)]"
      >
        <div className="flex items-center gap-4 mb-8">
          <div className="w-12 h-12 bg-zinc-50 rounded-2xl flex items-center justify-center border border-zinc-100 text-zinc-400">
            <UserIcon size={20} />
          </div>
          <h2 className="text-2xl font-serif font-bold text-zinc-900 tracking-tight">Account Details</h2>
        </div>

        <div className="space-y-6">
          <div className="group">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5 flex items-center gap-1.5">
              <Hash size={12} /> User ID
            </p>
            <p className="text-sm font-mono text-zinc-700 bg-zinc-50 px-3 py-2 rounded-xl border border-zinc-100 break-all">
              {user.id}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5 flex items-center gap-1.5">
                <UserIcon size={12} /> Gender
              </p>
              <p className="text-base font-medium text-zinc-900 capitalize">
                {user.gender || 'Not specified'}
              </p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5 flex items-center gap-1.5">
                <Calendar size={12} /> Account Created
              </p>
              <p className="text-sm font-medium text-zinc-700">
                {createdDate}
              </p>
            </div>
          </div>

          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5">
              Loyalty Tier
            </p>
            <Badge className="px-3 py-1 bg-amber-50 text-amber-600 border-amber-200 shadow-none font-bold uppercase tracking-widest text-[10px]">
              {user.loyalty_tier || 'Standard'}
            </Badge>
          </div>
        </div>
      </motion.div>

      {/* --- LIFETIME VALUE (SPEND) CARD --- */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="bg-zinc-900 text-white rounded-[2.5rem] p-8 md:p-10 shadow-2xl relative overflow-hidden"
      >
        {/* Decorative background flare */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center border border-white/10 text-zinc-300">
              <CreditCard size={20} />
            </div>
            <h2 className="text-2xl font-serif font-bold text-white tracking-tight">Lifetime Value</h2>
          </div>

          {loading ? (
            <div className="space-y-6">
              <Skeleton className="h-16 w-1/2 bg-white/10 rounded-2xl" />
              <div className="flex gap-4">
                <Skeleton className="h-12 w-1/3 bg-white/10 rounded-xl" />
                <Skeleton className="h-12 w-1/3 bg-white/10 rounded-xl" />
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-2">
                  Total Spend
                </p>
                <p className="text-5xl md:text-6xl font-serif font-bold text-white tracking-tighter">
                  ₹{Number(totalSpend).toLocaleString('en-IN')}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-sm">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-2 flex items-center gap-1.5">
                    <ShoppingBag size={12} /> Total Orders
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {orderCount}
                  </p>
                </div>

                <div className="bg-white/5 border border-white/10 rounded-2xl p-5 backdrop-blur-sm">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-2 flex items-center gap-1.5">
                    <TrendingUp size={12} /> Avg. Order Value
                  </p>
                  <p className="text-2xl font-bold text-white">
                    ₹{Number(aov).toLocaleString('en-IN')}
                  </p>
                </div>
              </div>

            </div>
          )}
        </div>
      </motion.div>

    </div>
  );
}