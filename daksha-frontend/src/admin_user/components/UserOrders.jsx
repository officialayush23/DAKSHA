import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShoppingBag, Calendar, ChevronRight, 
  CheckCircle2, Clock, Truck, XCircle, Package
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from 'sonner';

// --- Helper: Status Badge Styling ---
const getStatusConfig = (status) => {
  const s = (status || "").toLowerCase();
  switch (s) {
    case 'delivered':
      return { color: 'bg-emerald-50 text-emerald-600 border-emerald-200', icon: CheckCircle2 };
    case 'cancelled':
      return { color: 'bg-red-50 text-red-600 border-red-200', icon: XCircle };
    case 'shipped':
    case 'out_for_delivery':
      return { color: 'bg-blue-50 text-blue-600 border-blue-200', icon: Truck };
    case 'ready_for_pickup':
      return { color: 'bg-indigo-50 text-indigo-600 border-indigo-200', icon: Package };
    case 'created':
    case 'confirmed':
    case 'packed':
    default:
      return { color: 'bg-amber-50 text-amber-600 border-amber-200', icon: Clock };
  }
};

export default function UserOrders({ userId }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        const res = await AdminUserService.getUserOrders(userId);
        const fetchedOrders = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
        
        // Sort by newest first
        const sortedOrders = fetchedOrders.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        setOrders(sortedOrders);
      } catch (error) {
        console.error("Failed to load user orders", error);
        toast.error("Could not load the user's order history.");
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchOrders();
  }, [userId]);

  // --- RENDER HELPERS ---
  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-40 w-full rounded-[2rem] bg-zinc-50" />
        ))}
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] min-h-[400px] flex flex-col items-center justify-center text-center p-10">
        <div className="w-20 h-20 bg-zinc-50 rounded-full flex items-center justify-center mb-6 border border-zinc-100">
          <ShoppingBag size={32} className="text-zinc-300" strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-serif font-bold text-zinc-900 mb-2">No Order History</h3>
        <p className="text-zinc-500 max-w-sm">This customer hasn't placed any orders yet. Once they do, they will appear here.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <AnimatePresence>
        {orders.map((order, index) => {
          // Fallback extraction logic for robust rendering
          const orderId = order.id || order.order_id || "Unknown";
          const displayId = orderId.toString().slice(-8).toUpperCase();
          const total = order.total_amount || order.grand_total || 0;
          const items = Array.isArray(order.items) ? order.items : [];
          const date = order.created_at 
            ? new Date(order.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) 
            : "Recently";
          
          const { icon: StatusIcon, color: statusColor } = getStatusConfig(order.status);

          return (
            <motion.div
              key={orderId}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              className="group bg-white rounded-[2rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] p-6 md:p-8 hover:shadow-xl hover:border-zinc-200 transition-all duration-300"
            >
              <div className="flex flex-col lg:flex-row justify-between lg:items-center gap-6">
                
                {/* Left: Order Info */}
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-4 mb-3">
                    <h3 className="text-xl font-bold text-zinc-900">
                      Order #{displayId}
                    </h3>
                    <Badge className={`px-3 py-1 text-[10px] font-bold uppercase tracking-widest shadow-none border ${statusColor}`}>
                      <StatusIcon size={12} className="mr-1.5" />
                      {order.status ? order.status.replace(/_/g, ' ') : "Processing"}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center gap-6 text-sm font-medium text-zinc-500">
                    <span className="flex items-center gap-2">
                      <Calendar size={14} className="text-zinc-400" /> {date}
                    </span>
                    <span className="flex items-center gap-2">
                      <Package size={14} className="text-zinc-400" /> {items.length} {items.length === 1 ? 'Item' : 'Items'}
                    </span>
                  </div>
                </div>

                <div className="hidden lg:block h-12 w-px bg-zinc-100" />
                <Separator className="lg:hidden my-2 bg-zinc-100" />

                {/* Right: Price & Action */}
                <div className="flex items-center justify-between lg:justify-end gap-8 min-w-[200px]">
                  <div className="text-left lg:text-right">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1">Total</p>
                    <p className="text-2xl font-serif font-bold text-black tracking-tight">₹{Number(total).toLocaleString('en-IN')}</p>
                  </div>

                  <Link 
                    to={`/admin/orders/${orderId}`} // Links to your main global order management page
                    className="w-12 h-12 rounded-full bg-zinc-50 flex items-center justify-center text-zinc-400 group-hover:bg-zinc-900 group-hover:text-white transition-all duration-300"
                  >
                    <ChevronRight size={20} className="group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>

              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}