import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { OrderService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { 
  Package, ArrowRight, ArrowLeft, ChevronRight, 
  Calendar, CheckCircle2, Clock, XCircle, Truck
} from "lucide-react";
import { toast } from "sonner";

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

export default function OrdersPage() {
  // --- State ---
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  // ================= LOAD DATA =================
  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      try {
        const res = await OrderService.getAll();
        // Extract array securely regardless of API wrapping
        const fetchedOrders = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
        
        // Sort by newest first (assuming created_at exists, fallback to original order)
        const sortedOrders = fetchedOrders.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        setOrders(sortedOrders);
      } catch (e) {
        console.error("Orders load error", e);
        toast.error("Failed to load your order history.");
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  // ================= RENDER HELPERS =================
  if (loading) {
    return (
      <div className="w-full max-w-[1200px] mx-auto p-4 md:p-10 space-y-8 animate-pulse">
        <Skeleton className="h-16 w-1/3 rounded-2xl mb-12" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-64 w-full rounded-[2.5rem]" />)}
      </div>
    );
  }

  // --- EMPTY STATE ---
  if (orders.length === 0) {
    return (
      <div className="w-full max-w-[1200px] mx-auto min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
        <div className="w-32 h-32 bg-zinc-50 rounded-full flex items-center justify-center mb-8 border border-zinc-100 shadow-inner">
          <Package size={48} className="text-zinc-300" strokeWidth={1} />
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-zinc-900 mb-4 tracking-tight">No orders yet</h1>
        <p className="text-zinc-500 mb-10 text-lg max-w-md">Your order history is currently empty. Discover our latest collection and find something you love.</p>
        <Button asChild className="rounded-full px-10 py-7 text-lg bg-zinc-900 hover:bg-black text-white shadow-xl hover:scale-105 transition-all">
          <Link to="/dash/shop">
            Start Shopping <ArrowRight className="ml-2" />
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1200px] mx-auto bg-white min-h-screen pb-32 pt-6 px-4 md:px-10">
      
      {/* Top Nav */}
      <div className="mb-10">
        <Link to="/dash/shop" className="group flex items-center text-sm font-semibold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors w-fit">
          <ArrowLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Shop
        </Link>
      </div>

      <div className="flex items-baseline justify-between mb-12">
        <h1 className="text-5xl lg:text-6xl font-serif font-bold text-zinc-900 tracking-tight">Order History</h1>
        <span className="text-xl font-medium text-zinc-400">{orders.length} {orders.length === 1 ? 'Order' : 'Orders'}</span>
      </div>

      {/* --- ORDERS LIST --- */}
      <div className="space-y-8">
        <AnimatePresence>
          {orders.map((order, index) => {
            // Bulletproof data extraction
            const orderId = order.id || order.order_id || "Unknown";
            const total = order.total_amount || order.grand_total || 0;
            const items = Array.isArray(order.items) ? order.items : [];
            const date = order.created_at ? new Date(order.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : "Recently";
            
            const StatusIcon = getStatusConfig(order.status).icon;
            const statusColor = getStatusConfig(order.status).color;

            return (
              <motion.div
                key={orderId}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.5, ease: "easeOut" }}
                className="group block bg-white border border-zinc-200/60 rounded-[2.5rem] p-6 md:p-8 hover:shadow-[0_15px_40px_-15px_rgba(0,0,0,0.05)] hover:border-zinc-300 transition-all duration-500"
              >
                {/* --- CARD HEADER --- */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                  <div>
                    <p className="text-[10px] md:text-xs font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1 flex items-center gap-2">
                      <Calendar size={14} /> {date}
                    </p>
                    <h3 className="text-lg md:text-xl font-bold text-zinc-900">
                      Order #{orderId.toString().slice(-8).toUpperCase()}
                    </h3>
                  </div>
                  
                  <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-end">
                    <span className="text-2xl font-serif font-bold text-black tracking-tight">₹{total}</span>
                    <Badge className={`px-3 py-1.5 rounded-full border shadow-sm text-xs uppercase tracking-widest font-bold flex items-center gap-1.5 ${statusColor}`}>
                      <StatusIcon size={14} /> {order.status ? order.status.replace(/_/g, ' ') : "Processing"}
                    </Badge>
                  </div>
                </div>

                <Separator className="my-6 bg-zinc-100" />

                {/* --- ITEMS THUMBNAIL ROW --- */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                  
                  <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-hide max-w-full">
                    {items.slice(0, 4).map((item, idx) => {
                      const img = item.image_url || item.image || item.product?.image || "https://placehold.co/200x200/F8F9FA/a1a1aa?text=Item";
                      return (
                        <div key={idx} className="relative w-20 h-24 md:w-24 md:h-28 shrink-0 bg-[#F8F9FA] rounded-2xl overflow-hidden border border-zinc-100 flex items-center justify-center group-hover:bg-[#F0F2F5] transition-colors">
                          <img 
                            src={img} 
                            alt="Order Item" 
                            className="w-full h-full object-contain p-2 mix-blend-multiply"
                          />
                          {item.quantity > 1 && (
                            <span className="absolute top-1 right-1 bg-white/90 backdrop-blur-sm text-[9px] font-bold text-zinc-600 px-1.5 py-0.5 rounded-md shadow-sm border border-zinc-200">
                              x{item.quantity}
                            </span>
                          )}
                        </div>
                      )
                    })}
                    {items.length > 4 && (
                      <div className="w-20 h-24 md:w-24 md:h-28 shrink-0 bg-zinc-50 rounded-2xl border border-zinc-200 border-dashed flex flex-col items-center justify-center text-zinc-500">
                        <span className="text-lg font-bold">+{items.length - 4}</span>
                        <span className="text-[10px] uppercase tracking-widest font-semibold">More</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="w-full md:w-auto flex shrink-0">
                    <Button asChild variant="outline" className="w-full md:w-auto rounded-full h-14 px-8 border-2 border-zinc-200 text-zinc-700 hover:border-black hover:bg-black hover:text-white transition-all font-bold tracking-wide">
                      <Link to={`/dash/orders/${orderId}`}>
                        View Details <ChevronRight className="ml-2" size={18} />
                      </Link>
                    </Button>
                  </div>
                  
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

    </div>
  );
}