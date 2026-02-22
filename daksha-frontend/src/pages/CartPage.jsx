import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CartService, SessionService, CheckoutService, ProductService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

import { 
  ShoppingBag, Trash2, ArrowRight, Minus, Plus, 
  ShieldCheck, ArrowLeft, Loader2
} from "lucide-react";
import { toast } from "sonner";

const getErrorMessage = (error, fallbackMessage) => {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail[0]?.msg || fallbackMessage;
  }
  if (error?.response?.data?.message) return error.response.data.message;
  return fallbackMessage;
};

export default function CartPage() {
  const navigate = useNavigate();
  
  // --- State ---
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // ================= SMART LOAD DATA (ENRICHMENT) =================
  const loadCart = async () => {
    try {
      const sessRes = await SessionService.getActive().catch(() => null);
      const activeSessionId = sessRes?.data?.session_id || sessRes?.session_id || null;
      setSessionId(activeSessionId);

      // 1. Fetch raw cart
      const res = await CartService.get();
      let cartData = res.data || res || { items: [] };

      // 2. ENRICHMENT: Fetch live product details to get dynamic discounts
      if (cartData.items && cartData.items.length > 0) {
        // Get unique product IDs to avoid redundant API calls
        const uniqueProductIds = [...new Set(cartData.items.map(i => i.product_id).filter(Boolean))];
        
        // Fetch product details in parallel
        const productResponses = await Promise.all(
          uniqueProductIds.map(id => ProductService.getDetail(id).catch(() => null))
        );
        
        // Create a fast lookup map for variant details
        const variantLookup = {};
        productResponses.forEach(prod => {
          const p = prod?.data || prod;
          if (!p || !p.variants) return;
          p.variants.forEach(v => {
            variantLookup[v.variant_id] = {
              final_price: v.final_price || v.base_price,
              base_price: v.base_price,
              discount_percent: v.discount_percent || 0,
              image: v.images?.[0] || v.image_url || v.image || p.image
            };
          });
        });

        // 3. Merge live data back into cart items
        let enrichedSubtotal = 0;
        cartData.items = cartData.items.map(item => {
          const liveData = variantLookup[item.variant_id] || {};
          
          const finalPrice = liveData.final_price || item.base_price || 0;
          const basePrice = liveData.base_price || item.base_price || 0;
          const discount = liveData.discount_percent || 0;
          const itemTotal = finalPrice * item.quantity;
          
          enrichedSubtotal += itemTotal;

          return {
            ...item,
            live_final_price: finalPrice,
            live_base_price: basePrice,
            live_discount: discount,
            live_item_total: itemTotal,
            live_image: liveData.image || item.image_url
          };
        });

        // Override backend total with the correctly discounted total
        cartData.grand_total = enrichedSubtotal; 
      }

      setCart(cartData);
    } catch (e) {
      console.error("Cart load error", e);
      toast.error("Failed to load your bag.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
  }, []);

  // ================= ACTIONS =================
  const handleUpdateQuantity = async (variantId, newQuantity) => {
    if (newQuantity < 1) {
      handleRemoveItem(variantId);
      return;
    }

    setUpdatingId(variantId);
    try {
      await CartService.update(variantId, newQuantity, sessionId);
      await loadCart();
    } catch (e) {
      const errorMsg = getErrorMessage(e, "Could not update quantity.");
      if (errorMsg.toLowerCase().includes("inventory") || errorMsg.toLowerCase().includes("available")) {
        toast.warning(errorMsg);
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRemoveItem = async (variantId) => {
    setUpdatingId(variantId);
    try {
      await CartService.remove(variantId, sessionId);
      toast.success("Item removed from bag.");
      await loadCart();
    } catch (e) {
      const errorMsg = getErrorMessage(e, "Could not remove item.");
      toast.error(errorMsg);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleCheckout = async () => {
    setIsCheckingOut(true);
    try {
      const res = await CheckoutService.start();
      const checkoutId = res?.data?.checkout_id || res?.checkout_id || "new";
      navigate(`/dash/checkout/${checkoutId}`);
    } catch (e) {
      const errorMsg = getErrorMessage(e, "Failed to initiate checkout. Please try again.");
      toast.error(errorMsg);
      setIsCheckingOut(false);
    }
  };

  // ================= RENDER HELPERS =================
  const items = cart?.items || [];
  const grandTotal = cart?.grand_total || 0;
  const totalItemsCount = cart?.total_items || items.length;

  if (loading) {
    return (
      <div className="w-full max-w-[1400px] mx-auto p-4 md:p-10 grid lg:grid-cols-12 gap-16 animate-pulse">
        <div className="lg:col-span-8 space-y-8">
          <Skeleton className="h-16 w-1/3 rounded-2xl mb-10" />
          {[1, 2].map(i => <Skeleton key={i} className="h-48 w-full rounded-3xl" />)}
        </div>
        <div className="lg:col-span-4">
          <Skeleton className="h-96 w-full rounded-[3rem]" />
        </div>
      </div>
    );
  }

  // --- EMPTY STATE ---
  if (items.length === 0) {
    return (
      <div className="w-full max-w-[1400px] mx-auto min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
        <div className="w-32 h-32 bg-zinc-50 rounded-full flex items-center justify-center mb-8 border border-zinc-100 shadow-inner">
          <ShoppingBag size={48} className="text-zinc-300" strokeWidth={1} />
        </div>
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-zinc-900 mb-4 tracking-tight">Your bag is empty</h1>
        <p className="text-zinc-500 mb-10 text-lg">Looks like you haven't added anything to your bag yet.</p>
        <Button asChild className="rounded-full px-10 py-7 text-lg bg-zinc-900 hover:bg-black text-white shadow-xl hover:scale-105 transition-all">
          <Link to="/dash/shop">
            Explore Collection <ArrowRight className="ml-2" />
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1400px] mx-auto bg-white min-h-screen pb-32 pt-6 px-4 md:px-10">
      
      {/* Top Nav */}
      <div className="mb-10">
        <Link to="/dash/shop" className="group flex items-center text-sm font-semibold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors w-fit">
          <ArrowLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" /> Continue Shopping
        </Link>
      </div>

      <div className="flex items-baseline justify-between mb-12">
        <h1 className="text-5xl lg:text-6xl font-serif font-bold text-zinc-900 tracking-tight">My Bag</h1>
        <span className="text-xl font-medium text-zinc-400">
          {totalItemsCount} {totalItemsCount === 1 ? 'Item' : 'Items'}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-20">
        
        {/* ================= LEFT: CART ITEMS ================= */}
        <div className="lg:col-span-7 xl:col-span-8 space-y-6">
          <AnimatePresence>
            {items.map((item) => {
              // Extract Enriched Live Data
              const price = item.live_final_price || item.base_price || 0;
              const originalPrice = item.live_base_price || item.base_price || price;
              const itemTotal = item.live_item_total || (price * item.quantity);
              const discount = item.live_discount || 0;
              const imageUrl = item.live_image || "https://placehold.co/600x800/F8F9FA/a1a1aa?text=No+Image";
              
              const isUpdating = updatingId === item.variant_id;
              
              return (
                <motion.div 
                  key={item.variant_id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -50, scale: 0.95 }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                  className={`flex gap-6 p-4 rounded-[2.5rem] border border-zinc-100 transition-all group hover:bg-zinc-50/50 ${isUpdating ? 'opacity-50 pointer-events-none' : ''}`}
                >
                  {/* Premium Item Image */}
                  <Link to={`/dash/product/${item.product_id}`} className="shrink-0 relative">
                    <div className="w-32 md:w-48 aspect-[4/5] bg-[#F8F9FA] rounded-[2rem] overflow-hidden flex items-center justify-center relative">
                      {discount > 0 && (
                        <Badge className="absolute top-3 left-3 z-20 bg-gradient-to-r from-red-600 to-rose-500 text-white px-2 py-1 text-[8px] font-bold uppercase tracking-widest shadow-sm border-none">
                          {discount}% OFF
                        </Badge>
                      )}
                      <img 
                        src={imageUrl} 
                        alt={item.name} 
                        className="w-full h-full object-contain p-6 mix-blend-multiply group-hover:scale-110 transition-transform duration-700"
                      />
                    </div>
                  </Link>

                  {/* Item Details */}
                  <div className="flex flex-col flex-1 py-2 justify-between pr-2">
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <div className="text-[10px] md:text-xs uppercase tracking-[0.2em] text-zinc-400 font-bold mb-1.5">
                          {item.brand || "Brand"}
                        </div>
                        <Link to={`/dash/product/${item.product_id}`} className="hover:text-zinc-600 transition-colors">
                          <h3 className="text-xl md:text-2xl font-bold text-zinc-900 leading-tight mb-3 line-clamp-2">
                            {item.name}
                          </h3>
                        </Link>
                        
                        <div className="flex flex-wrap items-center gap-3 text-sm text-zinc-500 font-medium">
                          {item.color && (
                            <span className="flex items-center gap-1.5">
                              <span className="w-3 h-3 rounded-full border border-zinc-200" style={{ backgroundColor: item.color.toLowerCase() }} />
                              {item.color}
                            </span>
                          )}
                          {item.color && item.size && <span className="w-1.5 h-1.5 bg-zinc-300 rounded-full" />}
                          {item.size && <span>Size {item.size}</span>}
                        </div>
                      </div>
                      
                      <div className="text-right shrink-0">
                        <p className="text-2xl font-serif font-bold text-black tracking-tight">
                          ₹{itemTotal}
                        </p>
                        {item.quantity > 1 && (
                          <div className="flex flex-col items-end mt-1">
                            <p className="text-xs font-medium text-zinc-600">₹{price} each</p>
                          </div>
                        )}
                        {discount > 0 && item.quantity === 1 && (
                          <p className="text-sm font-medium text-zinc-400 line-through mt-1">
                            ₹{originalPrice}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Actions: Quantity & Remove */}
                    <div className="flex items-center justify-between mt-6">
                      
                      {/* Premium Quantity Selector */}
                      <div className="flex items-center bg-zinc-100 rounded-full p-1.5 border border-zinc-200/50">
                        <button 
                          onClick={() => handleUpdateQuantity(item.variant_id, item.quantity - 1)}
                          className="w-8 h-8 flex items-center justify-center rounded-full bg-white shadow-sm hover:shadow-md transition-all text-zinc-600 hover:text-black"
                        >
                          <Minus size={14} strokeWidth={2.5} />
                        </button>
                        <span className="w-10 text-center font-bold text-sm select-none text-black">
                          {item.quantity}
                        </span>
                        <button 
                          onClick={() => handleUpdateQuantity(item.variant_id, item.quantity + 1)}
                          className="w-8 h-8 flex items-center justify-center rounded-full bg-white shadow-sm hover:shadow-md transition-all text-zinc-600 hover:text-black"
                        >
                          <Plus size={14} strokeWidth={2.5} />
                        </button>
                      </div>

                      {/* Remove Button */}
                      <button 
                        onClick={() => handleRemoveItem(item.variant_id)}
                        className="text-xs font-bold uppercase tracking-widest text-zinc-400 hover:text-red-500 flex items-center gap-1.5 transition-colors p-2"
                      >
                        <Trash2 size={16} /> <span className="hidden md:inline">Remove</span>
                      </button>

                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>

        {/* ================= RIGHT: ORDER SUMMARY ================= */}
        <div className="lg:col-span-5 xl:col-span-4 relative">
          <div className="sticky top-32 bg-[#F8F9FA] rounded-[3rem] p-8 md:p-10 border border-zinc-100 shadow-[inset_0_0_50px_rgba(0,0,0,0.02)]">
            <h2 className="text-2xl font-serif font-bold text-zinc-900 mb-8 tracking-tight">Order Summary</h2>
            
            <div className="space-y-5 text-base font-medium text-zinc-600">
              <div className="flex justify-between items-center">
                <span>Items Subtotal</span>
                <span className="text-zinc-900">₹{grandTotal}</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Estimated Shipping</span>
                <span className="text-emerald-600 font-bold tracking-wider uppercase text-sm">
                  Free
                </span>
              </div>
            </div>

            <Separator className="my-8 bg-zinc-200/60" />

            <div className="flex justify-between items-end mb-10">
              <span className="text-lg font-bold text-zinc-900">Total</span>
              <div className="text-right">
                <span className="text-5xl font-serif font-bold text-black tracking-tight">₹{grandTotal}</span>
                <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-widest mt-2">Includes all taxes & discounts</p>
              </div>
            </div>

            <Button 
              onClick={handleCheckout} 
              disabled={isCheckingOut || items.length === 0}
              className="w-full h-16 rounded-full bg-zinc-900 hover:bg-black text-white text-lg font-bold tracking-wide shadow-[0_10px_40px_rgba(0,0,0,0.15)] transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
            >
              {isCheckingOut ? <Loader2 className="animate-spin mr-3" /> : null}
              {isCheckingOut ? "Processing..." : "Proceed to Checkout"}
            </Button>

            {/* Trust Badges */}
            <div className="mt-8 space-y-5">
              <div className="flex items-center gap-3 text-xs font-bold text-zinc-500 uppercase tracking-widest justify-center">
                <ShieldCheck size={18} className="text-zinc-400" /> Secure SSL Checkout
              </div>
              <div className="flex items-center justify-center gap-3">
                <div className="h-8 px-3 bg-white rounded-lg border border-zinc-200 shadow-sm flex items-center justify-center text-[10px] font-bold text-zinc-500">VISA</div>
                <div className="h-8 px-3 bg-white rounded-lg border border-zinc-200 shadow-sm flex items-center justify-center text-[10px] font-bold text-zinc-500">MC</div>
                <div className="h-8 px-3 bg-white rounded-lg border border-zinc-200 shadow-sm flex items-center justify-center text-[10px] font-bold text-zinc-500">RUPAY</div>
                <div className="h-8 px-3 bg-white rounded-lg border border-zinc-200 shadow-sm flex items-center justify-center text-[10px] font-bold text-zinc-500">UPI</div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}