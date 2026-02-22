import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShoppingCart, Clock, Package, 
  AlertCircle, CheckCircle2, Hash
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

// --- Helper: Determine Cart Status ---
const getCartStatus = (updatedAt) => {
  if (!updatedAt) return { label: 'Unknown', color: 'bg-zinc-100 text-zinc-600', icon: Clock };
  
  const lastUpdated = new Date(updatedAt);
  const now = new Date();
  const hoursDifference = (now - lastUpdated) / (1000 * 60 * 60);

  if (hoursDifference > 24) {
    return { label: 'Abandoned', color: 'bg-red-50 text-red-600 border-red-200', icon: AlertCircle };
  }
  return { label: 'Active', color: 'bg-emerald-50 text-emerald-600 border-emerald-200', icon: CheckCircle2 };
};

export default function UserCarts({ userId }) {
  const [carts, setCarts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCarts = async () => {
      try {
        setLoading(true);
        const res = await AdminUserService.getUserCarts(userId);
        const fetchedCarts = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
        
        // Sort by most recently updated
        const sorted = fetchedCarts.sort((a, b) => new Date(b.updated_at || 0) - new Date(a.updated_at || 0));
        setCarts(sorted);
      } catch (error) {
        console.error("Failed to load user carts", error);
        toast.error("Could not load the user's carts.");
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchCarts();
  }, [userId]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[1, 2].map(i => (
          <Skeleton key={i} className="h-64 w-full rounded-[2.5rem] bg-zinc-50" />
        ))}
      </div>
    );
  }

  if (carts.length === 0) {
    return (
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] min-h-[400px] flex flex-col items-center justify-center text-center p-10">
        <div className="w-20 h-20 bg-zinc-50 rounded-full flex items-center justify-center mb-6 border border-zinc-100">
          <ShoppingCart size={32} className="text-zinc-300" strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-serif font-bold text-zinc-900 mb-2">No Carts Found</h3>
        <p className="text-zinc-500 max-w-sm">This user doesn't have any active or abandoned carts.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <AnimatePresence>
        {carts.map((cart, index) => {
          const cartId = cart.id || "Unknown";
          const displayId = cartId.toString().slice(-8).toUpperCase();
          const items = Array.isArray(cart.items) ? cart.items : [];
          const totalItems = items.reduce((sum, item) => sum + (item.quantity || 1), 0);
          
          const updatedAt = cart.updated_at ? new Date(cart.updated_at) : new Date();
          const formattedDate = updatedAt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
          const formattedTime = updatedAt.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
          
          const status = getCartStatus(cart.updated_at);
          const StatusIcon = status.icon;

          return (
            <motion.div
              key={cartId}
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] p-8 hover:shadow-xl hover:border-zinc-200 transition-all duration-300 flex flex-col"
            >
              
              {/* Header: ID and Status */}
              <div className="flex justify-between items-start mb-8">
                <div>
                  <div className="w-12 h-12 rounded-2xl bg-zinc-50 border border-zinc-100 flex items-center justify-center text-zinc-900 mb-4 shadow-sm">
                    <ShoppingCart size={20} />
                  </div>
                  <h3 className="text-xl font-serif font-bold text-zinc-900 flex items-center gap-2">
                    Cart #{displayId}
                  </h3>
                </div>
                
                <Badge className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest shadow-none border ${status.color}`}>
                  <StatusIcon size={12} className="mr-1.5" />
                  {status.label}
                </Badge>
              </div>

              {/* Grid Details */}
              <div className="grid grid-cols-2 gap-6 mb-8 flex-1">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5 flex items-center gap-1.5">
                    <Clock size={12} /> Last Updated
                  </p>
                  <p className="text-sm font-bold text-zinc-700">{formattedTime}</p>
                  <p className="text-xs font-medium text-zinc-400">{formattedDate}</p>
                </div>
                
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5 flex items-center gap-1.5">
                    <Package size={12} /> Contents
                  </p>
                  <p className="text-sm font-bold text-zinc-700">{totalItems} Items Total</p>
                  <p className="text-xs font-medium text-zinc-400">{items.length} Unique Products</p>
                </div>
              </div>

              {/* Session / Item Footer */}
              <div className="pt-6 border-t border-zinc-50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Hash size={14} className="text-zinc-300" />
                  <span className="text-xs font-mono text-zinc-400">
                    Session: {cart.session_id ? cart.session_id.split('-')[0].toUpperCase() : 'N/A'}
                  </span>
                </div>
              </div>

            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}