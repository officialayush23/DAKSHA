import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useBasePath } from '../hooks/useBasePath';
import { OrderService, ProductService, SupportService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";

import { 
  Package, ArrowLeft, Calendar, 
  CheckCircle2, Clock, Truck, Store, 
  RotateCcw, X, Loader2, ChevronRight
} from "lucide-react";

// --- Helper: Status Badge Styling ---
const getStatusConfig = (status) => {
  const s = (status || "").toLowerCase();
  switch (s) {
    case 'delivered':
      return { color: 'bg-emerald-50 text-emerald-600 border-emerald-200', icon: CheckCircle2, text: 'Delivered' };
    case 'shipped':
      return { color: 'bg-blue-50 text-blue-600 border-blue-200', icon: Truck, text: 'Shipped' };
    case 'ready_for_pickup':
      return { color: 'bg-amber-50 text-amber-600 border-amber-200', icon: Store, text: 'Ready for Pickup' };
    case 'confirmed':
      return { color: 'bg-indigo-50 text-indigo-600 border-indigo-200', icon: CheckCircle2, text: 'Confirmed' };
    case 'packed':
      return { color: 'bg-zinc-100 text-zinc-600 border-zinc-200', icon: Package, text: 'Packed' };
    case 'cancelled':
      return { color: 'bg-red-50 text-red-600 border-red-200', icon: X, text: 'Cancelled' };
    default:
      return { color: 'bg-gray-50 text-gray-600 border-gray-200', icon: Clock, text: s.replace(/_/g, ' ') };
  }
};

export default function OrdersPage() {
  const navigate = useNavigate();
  const { basePath } = useBasePath();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  // --- Return Modal State ---
  const [returnModalOpen, setReturnModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [returnQty, setReturnQty] = useState(1);
  const [returnReason, setReturnReason] = useState("");
  const [submittingReturn, setSubmittingReturn] = useState(false);

  // ================= LOAD DATA & ENRICH PRODUCTS =================
  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await OrderService.getAll();
      
      // Unwrap Axios/FastAPI response safely
      let fetchedOrders = [];
      if (res?.data?.data && Array.isArray(res.data.data)) {
        fetchedOrders = res.data.data; 
      } else if (res?.data && Array.isArray(res.data)) {
        fetchedOrders = res.data; 
      } else if (Array.isArray(res)) {
        fetchedOrders = res;
      }

      // Step 2: Extract all unique variant IDs to fetch product details
      const uniqueVariantIds = [...new Set(
        fetchedOrders.flatMap(order => order.products?.map(p => p.variant_id) || [])
      )];

      // Step 3: Fetch details for all variants concurrently
      const productDetailsMap = {};
      await Promise.all(
        uniqueVariantIds.map(async (vId) => {
          if (!vId) return;
          try {
            const pRes = await ProductService.getDetail(vId);
            const pData = pRes?.data || pRes;
            if (pData) {
              productDetailsMap[vId] = {
                name: pData.name || "Premium Item",
                image: pData.image_url || pData.images?.[0] || "https://placehold.co/200x200/F8F9FA/a1a1aa?text=Item"
              };
            }
          } catch (e) {
            // Silently ignore individual product fetch failures
            productDetailsMap[vId] = { name: "Premium Item", image: "https://placehold.co/200x200/F8F9FA/a1a1aa?text=Item" };
          }
        })
      );

      // Step 4: Map product details back into the orders
      const enrichedOrders = fetchedOrders.map(order => ({
        ...order,
        products: (order.products || []).map(p => ({
          ...p,
          display_name: productDetailsMap[p.variant_id]?.name || "Premium Item",
          display_image: productDetailsMap[p.variant_id]?.image || "https://placehold.co/200x200/F8F9FA/a1a1aa?text=Item"
        }))
      }));

      setOrders(enrichedOrders);
    } catch (e) {
      console.error("Orders load error", e);
      toast.error("Failed to load order history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  // ================= RETURN ACTIONS =================
  const openReturnModal = (order, product) => {
    setSelectedItem({
      order_id: order.order_id,
      variant_id: product.variant_id,
      max_qty: product.qty,
      display_name: product.display_name,
      display_image: product.display_image
    });
    setReturnQty(1);
    setReturnReason("");
    setReturnModalOpen(true);
  };

  const handleReturnSubmit = async () => {
    if (!returnReason.trim()) return toast.error("Please provide a reason for the return.");
    if (returnQty < 1 || returnQty > selectedItem.max_qty) return toast.error("Invalid quantity.");

    setSubmittingReturn(true);
    try {
      await SupportService.requestReturn({
        order_id: selectedItem.order_id,
        product_variant_id: selectedItem.variant_id,
        quantity: parseInt(returnQty),
        reason: returnReason
      });

      toast.success("Return request submitted successfully!");
      setReturnModalOpen(false);
      // Optional: Refetch orders or redirect to returns page
      // navigate('/dash/returns');
    } catch (error) {
      const msg = error?.response?.data?.detail || "Could not submit return request.";
      toast.error(msg);
    } finally {
      setSubmittingReturn(false);
    }
  };


  // ================= RENDER HELPERS =================
  if (loading) {
    return (
      <div className="w-full max-w-[1000px] mx-auto p-4 md:p-10 space-y-6 animate-pulse">
        <Skeleton className="h-16 w-1/3 rounded-2xl mb-12" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-48 w-full rounded-[2rem]" />)}
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="w-full max-w-[1000px] mx-auto min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
        <div className="w-32 h-32 bg-zinc-50 rounded-full flex items-center justify-center mb-8 border border-zinc-100 shadow-inner">
          <Package size={48} className="text-zinc-300" strokeWidth={1} />
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-zinc-900 mb-4 tracking-tight">No Orders Yet</h1>
        <p className="text-zinc-500 mb-10 text-lg max-w-md">Looks like you haven't placed any orders. Discover our latest collection!</p>
        <Button
          onClick={() => navigate(`${basePath}/shop`)}
          className="rounded-full px-10 py-7 text-lg bg-zinc-900 hover:bg-black text-white shadow-xl hover:scale-105 transition-all"
        >
          Start Shopping <ChevronRight className="ml-2" />
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1000px] mx-auto bg-white min-h-screen pb-32 pt-6 px-4 md:px-10 relative">
      
      {/* Top Nav */}
      <div className="mb-10">
        <button
          onClick={() => navigate(`${basePath}/profile`)}
          className="group flex items-center text-sm font-semibold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors w-fit"
        >
          <ArrowLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Profile
        </button>
      </div>

      <div className="flex items-baseline justify-between mb-10">
        <h1 className="text-4xl lg:text-5xl font-serif font-bold text-zinc-900 tracking-tight">Order History</h1>
        <span className="text-sm font-bold uppercase tracking-widest text-zinc-400">{orders.length} Orders</span>
      </div>

      {/* --- ORDERS LIST --- */}
      <div className="space-y-8">
        <AnimatePresence>
          {orders.map((order, index) => {
            const StatusIcon = getStatusConfig(order.status).icon;
            const statusConfig = getStatusConfig(order.status);
            
            // Parse Date
            const d = new Date(order.created_at);
            const dateStr = d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

            return (
              <motion.div
                key={order.order_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
                className="bg-white border border-zinc-200/80 rounded-[2rem] p-6 md:p-8 hover:shadow-lg transition-all duration-300"
              >
                {/* Order Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-100 pb-6 mb-6">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <p className="text-sm font-bold uppercase tracking-widest text-zinc-400">Order #{order.order_id.slice(0, 8)}</p>
                      <Badge className={`px-2.5 py-1 rounded-md border shadow-none text-[10px] uppercase tracking-widest font-bold flex items-center gap-1 ${statusConfig.color}`}>
                        <StatusIcon size={12} /> {statusConfig.text}
                      </Badge>
                    </div>
                    <p className="text-sm text-zinc-500 font-medium flex items-center gap-2">
                      <Calendar size={14} /> Placed on {dateStr}
                    </p>
                  </div>
                  <div className="text-left md:text-right">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1">Total</p>
                    <p className="text-2xl font-serif font-bold text-zinc-900">₹{order.total}</p>
                  </div>
                </div>

                {/* Products List */}
                <div className="space-y-4">
                  {order.products?.map((product, idx) => (
                    <div key={`${product.variant_id}-${idx}`} className="flex items-center justify-between gap-4 p-4 rounded-2xl hover:bg-zinc-50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-16 h-16 shrink-0 bg-[#F8F9FA] rounded-xl overflow-hidden border border-zinc-100 flex items-center justify-center p-1 relative">
                          <img src={product.display_image} alt="Product" className="w-full h-full object-contain mix-blend-multiply" />
                        </div>
                        <div>
                          <h4 className="font-bold text-zinc-900 line-clamp-1">{product.display_name}</h4>
                          <p className="text-xs text-zinc-500 mt-1">Qty: {product.qty} • ₹{product.price}</p>
                        </div>
                      </div>
                      
                      {/* ACTION BUTTONS (Only allow returns if DELIVERED) */}
                      {order.status.toLowerCase() === 'delivered' && (
                        <Button 
                          onClick={() => openReturnModal(order, product)}
                          variant="outline" 
                          size="sm"
                          className="rounded-xl border-zinc-200 text-zinc-700 hover:text-black hover:border-black font-bold tracking-wide text-xs"
                        >
                          <RotateCcw size={14} className="mr-2" /> Return Item
                        </Button>
                      )}
                    </div>
                  ))}
                  
                  {(!order.products || order.products.length === 0) && (
                    <p className="text-sm text-zinc-500 italic">No products found in this order.</p>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* ================= RETURN MODAL ================= */}
      <AnimatePresence>
        {returnModalOpen && selectedItem && (
          <>
            {/* Backdrop */}
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setReturnModalOpen(false)}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
            />
            
            {/* Modal */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }} 
              animate={{ opacity: 1, scale: 1, y: 0 }} 
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md bg-white rounded-[2rem] shadow-2xl p-8 z-50 border border-zinc-100"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-serif text-2xl font-bold">Request Return</h3>
                <button onClick={() => setReturnModalOpen(false)} className="text-zinc-400 hover:text-black transition-colors">
                  <X size={24} />
                </button>
              </div>

              <div className="flex gap-4 items-center mb-6 p-4 bg-zinc-50 rounded-2xl border border-zinc-100">
                <img src={selectedItem.display_image} className="w-12 h-12 rounded-lg object-cover mix-blend-multiply" alt="Item" />
                <div>
                  <p className="font-bold text-sm text-zinc-900 line-clamp-1">{selectedItem.display_name}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">Order #{selectedItem.order_id.slice(0,8)}</p>
                </div>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="text-xs font-bold uppercase tracking-widest text-zinc-500 mb-2 block">Quantity to Return</label>
                  <Input 
                    type="number" 
                    min="1" 
                    max={selectedItem.max_qty} 
                    value={returnQty}
                    onChange={(e) => setReturnQty(e.target.value)}
                    className="h-12 rounded-xl border-zinc-200 focus-visible:ring-black"
                  />
                  <p className="text-[10px] text-zinc-400 mt-1">Max eligible quantity: {selectedItem.max_qty}</p>
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-widest text-zinc-500 mb-2 block">Reason for Return</label>
                  <Input 
                    type="text" 
                    placeholder="e.g. Size issue, damaged, changed mind..." 
                    value={returnReason}
                    onChange={(e) => setReturnReason(e.target.value)}
                    className="h-12 rounded-xl border-zinc-200 focus-visible:ring-black"
                  />
                </div>

                <Button 
                  onClick={handleReturnSubmit}
                  disabled={submittingReturn || !returnReason.trim()}
                  className="w-full h-14 rounded-full bg-black hover:bg-zinc-800 text-white font-bold tracking-[0.15em] uppercase text-sm mt-4 transition-all"
                >
                  {submittingReturn ? <Loader2 className="animate-spin" /> : "Submit Return Request"}
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

    </div>
  );
}