import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SupportService, ProductService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

import { 
  PackageMinus, ArrowLeft, Calendar, 
  CheckCircle2, Clock, XCircle, ArrowRight, Loader2, RefreshCcw
} from "lucide-react";
import { toast } from "sonner";

// --- Helper: Status Badge Styling ---
const getStatusConfig = (status) => {
  const s = (status || "").toLowerCase();
  switch (s) {
    case 'approved':
    case 'completed':
      return { color: 'bg-emerald-50 text-emerald-600 border-emerald-200', icon: CheckCircle2 };
    case 'cancelled':
    case 'rejected':
      return { color: 'bg-red-50 text-red-600 border-red-200', icon: XCircle };
    case 'requested':
    case 'pending':
    default:
      return { color: 'bg-amber-50 text-amber-600 border-amber-200', icon: Clock };
  }
};

export default function ReturnsPage() {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState(null);

  // ================= LOAD DATA =================
  const fetchReturns = async () => {
    setLoading(true);
    try {
      const res = await SupportService.getMyReturns(0, 50);
      
      // 👇 FIXED: Securely unwrap the nested Axios/FastAPI response!
      let fetchedReturns = [];
      if (res?.data?.data && Array.isArray(res.data.data)) {
        fetchedReturns = res.data.data; // Matches: { success: true, data: [...] }
      } else if (res?.data && Array.isArray(res.data)) {
        fetchedReturns = res.data; // Fallback: [...]
      }
      
      const enrichedReturns = await Promise.all(
        fetchedReturns.map(async (ret) => {
          let imageUrl = "https://placehold.co/200x200/F8F9FA/a1a1aa?text=Item";
          let productName = "Returned Item";
          
          try {
            const prodRes = await ProductService.getDetail(ret.product_variant_id);
            const pData = prodRes?.data || prodRes;
            if (pData) {
              productName = pData.name || productName;
              imageUrl = pData.image_url || pData.images?.[0] || imageUrl;
            }
          } catch (e) {
            // Silently ignore if product details cannot be fetched
          }

          return {
            ...ret,
            display_name: productName,
            display_image: imageUrl
          };
        })
      );

      setReturns(enrichedReturns);
    } catch (e) {
      console.error("Returns load error", e);
      toast.error("Failed to load your return history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturns();
  }, []);

  // ================= ACTIONS =================
  const handleCancelReturn = async (returnId) => {
    setCancellingId(returnId);
    try {
      await SupportService.cancelReturn(returnId, "Changed my mind");
      toast.success("Return request cancelled successfully.");
      
      setReturns(prev => 
        prev.map(r => r.id === returnId ? { ...r, status: 'cancelled' } : r)
      );
    } catch (error) {
      const msg = error?.response?.data?.detail || "Could not cancel return.";
      toast.error(msg);
    } finally {
      setCancellingId(null);
    }
  };

  // ================= RENDER HELPERS =================
  if (loading) {
    return (
      <div className="w-full max-w-[1000px] mx-auto p-4 md:p-10 space-y-6 animate-pulse">
        <Skeleton className="h-16 w-1/3 rounded-2xl mb-12" />
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-40 w-full rounded-[2rem]" />)}
      </div>
    );
  }

  // --- EMPTY STATE ---
  if (returns.length === 0) {
    return (
      <div className="w-full max-w-[1000px] mx-auto min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
        <div className="w-32 h-32 bg-zinc-50 rounded-full flex items-center justify-center mb-8 border border-zinc-100 shadow-inner">
          <PackageMinus size={48} className="text-zinc-300" strokeWidth={1} />
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-zinc-900 mb-4 tracking-tight">No Returns</h1>
        <p className="text-zinc-500 mb-10 text-lg max-w-md">You haven't requested any returns yet. Need help with a recent order?</p>
        <Button asChild className="rounded-full px-10 py-7 text-lg bg-zinc-900 hover:bg-black text-white shadow-xl hover:scale-105 transition-all">
          <Link to="/dash/orders">
            View My Orders <ArrowRight className="ml-2" />
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1000px] mx-auto bg-white min-h-screen pb-32 pt-6 px-4 md:px-10">
      
      {/* Top Nav */}
      <div className="mb-10">
        <Link to="/dash/profile" className="group flex items-center text-sm font-semibold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors w-fit">
          <ArrowLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Profile
        </Link>
      </div>

      <div className="flex items-baseline justify-between mb-10">
        <h1 className="text-4xl lg:text-5xl font-serif font-bold text-zinc-900 tracking-tight">My Returns</h1>
        <span className="text-sm font-bold uppercase tracking-widest text-zinc-400">{returns.length} Requests</span>
      </div>

      {/* --- RETURNS LIST --- */}
      <div className="space-y-6">
        <AnimatePresence>
          {returns.map((ret, index) => {
            const StatusIcon = getStatusConfig(ret.status).icon;
            const statusColor = getStatusConfig(ret.status).color;
            const isCancelling = cancellingId === ret.id;
            
            // Format Date
            let date = "Recently";
            if (ret.created_at) {
               const d = new Date(ret.created_at);
               date = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            }

            return (
              <motion.div
                key={ret.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
                className="bg-white border border-zinc-200/80 rounded-[2rem] p-6 hover:shadow-md transition-all duration-300"
              >
                <div className="flex flex-col md:flex-row gap-6">
                  
                  {/* Left: Product Thumbnail & Basic Info */}
                  <div className="flex flex-1 gap-5">
                    <div className="w-24 h-24 shrink-0 bg-[#F8F9FA] rounded-2xl overflow-hidden border border-zinc-100 flex items-center justify-center p-2 relative">
                      <img 
                        src={ret.display_image} 
                        alt="Returned Item" 
                        className="w-full h-full object-contain mix-blend-multiply"
                      />
                      {ret.quantity > 1 && (
                        <span className="absolute bottom-1 right-1 bg-white/90 backdrop-blur-sm text-[9px] font-bold text-zinc-600 px-1.5 py-0.5 rounded-md shadow-sm border border-zinc-200">
                          x{ret.quantity}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex flex-col justify-center">
                      <div className="flex items-center gap-3 mb-2">
                        <Badge className={`px-2.5 py-1 rounded-md border shadow-none text-[10px] uppercase tracking-widest font-bold flex items-center gap-1 ${statusColor}`}>
                          <StatusIcon size={12} /> {ret.status ? ret.status.replace(/_/g, ' ') : "Processing"}
                        </Badge>
                        <p className="text-xs font-bold uppercase tracking-widest text-zinc-400 flex items-center gap-1.5">
                          <Calendar size={12} /> {date}
                        </p>
                      </div>

                      <h3 className="text-lg font-bold text-zinc-900 leading-snug line-clamp-1">
                        {ret.display_name}
                      </h3>
                      
                      <div className="mt-2 space-y-0.5 text-sm">
                        <p className="text-zinc-500 font-medium">
                          <span className="text-zinc-400 text-xs uppercase tracking-widest mr-2">Reason:</span> 
                          {ret.reason || "Not specified"}
                        </p>
                        <p className="text-zinc-500 font-medium">
                          <span className="text-zinc-400 text-xs uppercase tracking-widest mr-2">Order ID:</span> 
                          <Link to={`/dash/orders/${ret.order_id}`} className="hover:text-black hover:underline transition-all">
                            #{ret.order_id.slice(0, 8).toUpperCase()}
                          </Link>
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Right: Actions */}
                  <div className="flex items-center md:items-start justify-end md:border-l md:border-zinc-100 md:pl-6 shrink-0">
                    {ret.status === 'requested' ? (
                      <Button 
                        variant="outline" 
                        onClick={() => handleCancelReturn(ret.id)}
                        disabled={isCancelling}
                        className="w-full md:w-auto rounded-xl border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300 font-bold tracking-wide transition-all"
                      >
                        {isCancelling ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <RefreshCcw className="mr-2 h-4 w-4" />}
                        Cancel Return
                      </Button>
                    ) : (
                      <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest bg-zinc-50 px-4 py-2 rounded-lg border border-zinc-100">
                        No Actions Available
                      </div>
                    )}
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