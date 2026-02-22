import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Heart, 
  ShoppingBag, 
  Trash2, 
  ArrowRight, 
  Loader2,
  Sparkles,
  Check
} from 'lucide-react';
import { 
  UserService,
  ProductService, 
  CartService, 
  SessionService 
} from '../lib/api';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { toast } from 'sonner';

export default function WishlistPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);
  const [successId, setSuccessId] = useState(null); // New state for success animation

  const loadWishlist = async () => {
    try {
      setLoading(true);
      const wishRes = await UserService.getWishlist();
      const wishData = wishRes.data || wishRes;

      if (!wishData.items || wishData.items.length === 0) {
        setItems([]);
        return;
      }

      const productRes = await ProductService.listProducts({ limit: 200 });
      const feed = productRes.data || productRes;
      const feedMap = {};
      const feedArray = Array.isArray(feed) ? feed : (feed.items || []);
      feedArray.forEach(p => { if (p.variant_id) feedMap[p.variant_id] = p; });

      const enriched = wishData.items.map(item => {
        const live = feedMap[item.variant_id];
        return {
          ...item,
          live_price: live?.final_price || item.base_price,
          live_base_price: live?.base_price || item.base_price,
          live_discount: live?.discount_percent || 0,
          live_image: live?.image || item.image_url,
          offer_name: live?.offer_name
        };
      });

      setItems(enriched);
    } catch (error) {
      toast.error("Failed to load wishlist");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadWishlist(); }, []);

  const handleRemove = async (e, variantId) => {
    e.preventDefault();
    e.stopPropagation();
    setActionId(variantId);
    try {
      await UserService.removeFromWishlist(variantId);
      setItems(prev => prev.filter(i => i.variant_id !== variantId));
      toast.success("Removed from wishlist");
    } catch (error) {
      toast.error("Failed to remove item");
    } finally {
      setActionId(null);
    }
  };

  const handleAddToCart = async (e, item) => {
    e.preventDefault();
    e.stopPropagation();
    
    setActionId(item.variant_id);
    try {
      const sessRes = await SessionService.getActive();
      const sessionId = sessRes?.data?.session_id || sessRes?.session_id;
      
      await CartService.add(item.variant_id, 1, sessionId);
      
      // Trigger Success Animation
      setSuccessId(item.variant_id);
      setTimeout(() => setSuccessId(null), 2000); // Reset after 2 seconds

      toast.success(`${item.name} added to bag! 🛍️`);
      UserService.captureEvent('add_to_cart', 'product_variant', item.variant_id).catch(() => {});
    } catch (error) {
      toast.error("Could not add to bag");
    } finally {
      setActionId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 space-y-12 max-w-[1600px] mx-auto">
        <Skeleton className="h-20 w-64 rounded-3xl" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="aspect-[4/5] rounded-[2rem]" />)}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-6">
        <div className="w-24 h-24 bg-zinc-50 rounded-full flex items-center justify-center mb-6 border border-zinc-100">
          <Heart size={40} className="text-zinc-200" />
        </div>
        <h1 className="text-4xl font-serif font-bold mb-3">Your wishlist is empty</h1>
        <p className="text-zinc-500 mb-8 max-w-sm">Save items you love here and they'll be waiting for you.</p>
        <Button asChild className="rounded-full px-10 py-7 bg-black text-white hover:scale-105 transition-all shadow-xl">
          <Link to="/dash/shop">Explore Collection <ArrowRight size={18} className="ml-2" /></Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto p-4 md:p-10 space-y-16 pb-24">
      <header>
        <h1 className="text-6xl md:text-8xl font-serif font-bold tracking-tighter text-zinc-900">Wishlist</h1>
        <p className="text-zinc-400 mt-4 flex items-center gap-2 text-xl font-medium">
          <Sparkles size={20} className="text-amber-500" /> {items.length} items curated for you.
        </p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-x-10 gap-y-16">
        <AnimatePresence mode="popLayout">
          {items.map((item, i) => (
            <motion.div
              key={item.variant_id}
              layout
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
              transition={{ delay: i * 0.05, duration: 0.5 }}
              className="group relative h-full flex flex-col"
            >
              <Link to={`/dash/product/${item.product_id}`} className="block h-full flex flex-col">
                <Card className="border-none bg-transparent shadow-none h-full flex flex-col">
                  
                  {/* --- IMAGE SECTION --- */}
                  <div className="relative aspect-[4/5] bg-[#F8F9FA] rounded-[2.5rem] overflow-hidden mb-6 flex items-center justify-center transition-all duration-700 group-hover:bg-[#F2F4F7] group-hover:shadow-[0_30px_60px_-15px_rgba(0,0,0,0.12)]">
                    
                    {item.live_discount > 0 && (
                      <Badge className="absolute top-6 left-6 z-20 bg-gradient-to-r from-red-600 to-rose-500 text-white px-4 py-2 text-[10px] font-bold uppercase tracking-[0.2em] shadow-lg border-none">
                        {item.live_discount}% OFF
                      </Badge>
                    )}

                    <img
                      src={item.live_image}
                      alt={item.name}
                      className="w-full h-full object-contain p-12 mix-blend-multiply group-hover:scale-110 transition-transform duration-[2s] ease-out"
                    />

                    {/* Trash Button */}
                    <button 
                      onClick={(e) => handleRemove(e, item.variant_id)}
                      className="absolute top-6 right-6 z-30 p-4 rounded-full bg-white/90 backdrop-blur-md shadow-sm border border-white text-zinc-400 hover:text-red-500 hover:scale-110 transition-all duration-300 active:scale-90"
                    >
                      {actionId === item.variant_id && !successId ? (
                        <Loader2 size={18} className="animate-spin" />
                      ) : (
                        <Trash2 size={18} />
                      )}
                    </button>

                    {/* Bottom Quick Add Button */}
                    <div className="absolute bottom-6 left-6 right-6 translate-y-4 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-500 ease-out z-20">
                      <motion.button 
                        whileTap={{ scale: 0.95 }}
                        onClick={(e) => handleAddToCart(e, item)}
                        disabled={actionId === item.variant_id}
                        className={`w-full py-5 rounded-2xl font-bold tracking-widest text-xs uppercase flex items-center justify-center gap-3 shadow-2xl transition-all duration-500 ${
                          successId === item.variant_id 
                          ? "bg-emerald-500 text-white shadow-emerald-200" 
                          : "bg-black/90 backdrop-blur-3xl text-white hover:bg-black"
                        }`}
                      >
                        {actionId === item.variant_id && !successId ? (
                          <Loader2 size={18} className="animate-spin text-white" />
                        ) : successId === item.variant_id ? (
                          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="flex items-center gap-2">
                            <Check size={18} strokeWidth={3} /> Added
                          </motion.div>
                        ) : (
                          <>
                            <ShoppingBag size={18} /> Quick Add
                          </>
                        )}
                      </motion.button>
                    </div>
                  </div>

                  {/* --- DETAILS SECTION --- */}
                  <CardContent className="p-0 space-y-3 flex-1 px-2">
                    <div className="text-[11px] uppercase tracking-[0.3em] text-zinc-400 font-black">
                      {item.brand || "DAKSHA"}
                    </div>
                    <h3 className="font-bold text-2xl text-zinc-900 leading-tight group-hover:text-zinc-600 transition-colors line-clamp-2">
                      {item.name}
                    </h3>
                    <div className="flex gap-2.5 mt-2">
                       <span className="text-[11px] bg-white border border-zinc-100 px-3 py-1.5 rounded-lg text-zinc-500 font-bold uppercase tracking-tighter shadow-sm">Size {item.size}</span>
                       <span className="text-[11px] bg-white border border-zinc-100 px-3 py-1.5 rounded-lg text-zinc-500 font-bold uppercase tracking-tighter shadow-sm">{item.color}</span>
                    </div>
                  </CardContent>

                  <CardFooter className="p-0 pt-6 flex items-baseline gap-3 mt-auto px-2">
                    <span className="font-serif text-3xl font-bold text-black tracking-tight">
                      ₹{item.live_price}
                    </span>
                    {item.live_discount > 0 && (
                      <span className="text-base font-medium text-zinc-300 line-through">
                        ₹{item.live_base_price}
                      </span>
                    )}
                  </CardFooter>
                </Card>
              </Link>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}