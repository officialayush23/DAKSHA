import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { OrderService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { 
  Package, ArrowRight, ArrowLeft, ChevronDown, ChevronUp,
  Calendar, CheckCircle2, Clock, XCircle, Truck, MapPin, Store, MessageSquare
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
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // State for expanded order details
  const [expandedId, setExpandedId] = useState(null);
  const [orderDetailsCache, setOrderDetailsCache] = useState({});
  const [detailsLoading, setDetailsLoading] = useState(false);

  // ================= LOAD ALL ORDERS =================
  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      try {
        const res = await OrderService.getAll();
        const fetchedOrders = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
        
        // Sort by newest first
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

  // ================= TOGGLE DETAILS =================
  const handleToggleDetails = async (orderId) => {
    if (expandedId === orderId) {
      setExpandedId(null); // Collapse if already open
      return;
    }

    setExpandedId(orderId);

    // If we haven't fetched details for this order yet, fetch them now
    if (!orderDetailsCache[orderId]) {
      setDetailsLoading(true);
      try {
        const [detailRes, feedbackRes] = await Promise.all([
          OrderService.getDetail(orderId).catch(() => ({ data: {} })),
          OrderService.getFeedbackStatus(orderId).catch(() => ({ data: { feedback_requested: false } }))
        ]);

        const detailData = detailRes?.data || detailRes || {};
        const feedbackData = feedbackRes?.data || feedbackRes || {};

        setOrderDetailsCache(prev => ({
          ...prev,
          [orderId]: {
            ...detailData,
            feedback_requested: feedbackData.feedback_requested
          }
        }));
      } catch (error) {
        toast.error("Failed to load full order details.");
      } finally {
        setDetailsLoading(false);
      }
    }
  };

  // ================= RENDER HELPERS =================
  if (loading) {
    return (
      <div className="w-full max-w-[900px] mx-auto p-4 md:p-10 space-y-6 animate-pulse">
        <Skeleton className="h-16 w-1/3 rounded-2xl mb-12" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full rounded-[2rem]" />)}
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="w-full max-w-[900px] mx-auto min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
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
    <div className="w-full max-w-[900px] mx-auto bg-white min-h-screen pb-32 pt-6 px-4 md:px-10">
      
      {/* Top Nav */}
      <div className="mb-10">
        <Link to="/dash/shop" className="group flex items-center text-sm font-semibold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors w-fit">
          <ArrowLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Shop
        </Link>
      </div>

      <div className="flex items-baseline justify-between mb-10">
        <h1 className="text-4xl lg:text-5xl font-serif font-bold text-zinc-900 tracking-tight">Order History</h1>
      </div>

      {/* --- CLEAN ORDERS LIST --- */}
      <div className="space-y-6">
        {orders.map((order, index) => {
          const orderId = order.order_id || order.id || "Unknown";
          const total = order.total || order.total_amount || 0;
          const products = order.products || [];
          const totalItems = products.reduce((acc, p) => acc + (p.qty || 1), 0);
          
          let date = "Recently";
          if (order.created_at) {
             const d = new Date(order.created_at);
             date = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
          }
          
          const StatusIcon = getStatusConfig(order.status).icon;
          const statusColor = getStatusConfig(order.status).color;
          
          const isExpanded = expandedId === orderId;
          const details = orderDetailsCache[orderId];

          return (
            <motion.div
              key={orderId}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
              className="bg-white border border-zinc-200/80 rounded-[1.5rem] overflow-hidden hover:shadow-md transition-all duration-300"
            >
              {/* SUMMARY HEADER (Clickable) */}
              <div 
                onClick={() => handleToggleDetails(orderId)}
                className="p-6 cursor-pointer flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white"
              >
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <p className="text-xs font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-1.5">
                      <Calendar size={12} /> {date}
                    </p>
                    <span className="w-1 h-1 rounded-full bg-zinc-300"></span>
                    <p className="text-xs font-bold text-zinc-500">
                      {totalItems} {totalItems === 1 ? 'Item' : 'Items'}
                    </p>
                  </div>
                  <h3 className="text-lg font-bold text-zinc-900 font-mono tracking-tight">
                    #{orderId.toString().slice(0, 8).toUpperCase()}
                  </h3>
                </div>
                
                <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto gap-3">
                  <span className="text-xl font-serif font-bold text-black">
                    ₹{total}
                  </span>
                  <div className="flex items-center gap-3">
                    <Badge className={`px-2.5 py-1 rounded-md border shadow-none text-[10px] uppercase tracking-widest font-bold flex items-center gap-1 ${statusColor}`}>
                      <StatusIcon size={12} /> {order.status ? order.status.replace(/_/g, ' ') : "Processing"}
                    </Badge>
                    <div className="w-8 h-8 rounded-full bg-zinc-50 flex items-center justify-center text-zinc-500 border border-zinc-200">
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>
                </div>
              </div>

              {/* EXPANDED DETAILS SECTION */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-zinc-100 bg-[#FDFDFD]"
                  >
                    <div className="p-6">
                      {detailsLoading && !details ? (
                        <div className="py-4 flex justify-center text-zinc-400">
                          <Skeleton className="h-20 w-full rounded-xl" />
                        </div>
                      ) : details ? (
                        <div className="space-y-6">
                          
                          {/* Fulfillment Info */}
                          <div className="flex items-start gap-3 bg-zinc-50 p-4 rounded-xl border border-zinc-100">
                            {details.fulfillment_type === 'pickup' ? (
                              <Store className="text-zinc-500 mt-0.5" size={20} />
                            ) : (
                              <MapPin className="text-zinc-500 mt-0.5" size={20} />
                            )}
                            <div>
                              <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1">
                                {details.fulfillment_type === 'pickup' ? 'Store Pickup' : 'Delivery Address'}
                              </p>
                              <p className="text-sm font-medium text-zinc-900 leading-relaxed">
                                {details.delivery_address || "Address pending confirmation..."}
                              </p>
                            </div>
                          </div>

                          {/* Items List (Using order.products as fallback if detail.items is empty) */}
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-3">Purchased Items</p>
                            <div className="space-y-3">
                              {products.map((item, idx) => (
                                <div key={idx} className="flex justify-between items-center py-2 border-b border-zinc-100 last:border-0">
                                  <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-zinc-100 rounded-lg flex items-center justify-center text-zinc-400">
                                      <Package size={16} />
                                    </div>
                                    <div>
                                      <p className="text-sm font-bold text-zinc-900">Product SKU: {item.variant_id.slice(0, 6).toUpperCase()}</p>
                                      <p className="text-xs text-zinc-500">Qty: {item.qty}</p>
                                    </div>
                                  </div>
                                  <p className="text-sm font-bold text-zinc-900">₹{item.price * item.qty}</p>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Feedback Banner */}
                          {details.feedback_requested && (
                            <div className="flex items-center justify-between bg-blue-50 border border-blue-100 p-4 rounded-xl">
                              <div className="flex items-center gap-3">
                                <MessageSquare size={18} className="text-blue-500" />
                                <p className="text-sm font-medium text-blue-900">How was your experience?</p>
                              </div>
                              <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded-full text-xs font-bold uppercase tracking-widest">
                                Leave Feedback
                              </Button>
                            </div>
                          )}

                        </div>
                      ) : (
                        <p className="text-center text-zinc-500 text-sm py-4">Could not load details.</p>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

    </div>
  );
}