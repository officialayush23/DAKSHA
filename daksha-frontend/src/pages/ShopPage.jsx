import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ProductService, CartService, UserService, SessionService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

import { 
  Search, Loader2, Sparkles, Flame, 
  Heart, ShoppingBag, ArrowRight 
} from "lucide-react";
import { toast } from "sonner";

const CATEGORIES = ["All", "Shoes", "Clothing", "Accessories", "Home", "Sports"];

const getUniqueProducts = (items) => {
  if (!Array.isArray(items)) return [];
  const uniqueMap = new Map();
  items.forEach(item => {
    if (item && item.product_id && !uniqueMap.has(item.product_id)) {
      uniqueMap.set(item.product_id, item);
    }
  });
  return Array.from(uniqueMap.values());
};

export default function ShopPage() {
  const [recommended, setRecommended] = useState([]);
  const [trending, setTrending] = useState([]);
  const [items, setItems] = useState([]);
  const [wishlistIds, setWishlistIds] = useState(new Set());
  const [sessionId, setSessionId] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  useEffect(() => {
    bootstrap();
  }, []);

  const bootstrap = async () => {
    setLoading(true);
    try {
      const sessRes = await SessionService.getActive().catch(() => null);
      const activeSessionId = sessRes?.data?.session_id || sessRes?.session_id || null;
      setSessionId(activeSessionId);

      const [feedRes, trendRes, listRes, wlRes] = await Promise.all([
        ProductService.getFeed().catch(() => ({ data: [] })),
        ProductService.getTrending().catch(() => ({ data: [] })),
        ProductService.listProducts({ limit: 100 }).catch(() => ({ data: [] })),
        UserService.getWishlist().catch(() => ({ data: { items: [] } }))
      ]);

      setRecommended(getUniqueProducts(feedRes?.data || feedRes));
      setTrending(getUniqueProducts(trendRes?.data || trendRes));
      setItems(getUniqueProducts(listRes?.data || listRes));
      
      const wlItems = wlRes?.data?.items || wlRes?.items || [];
      const wIds = wlItems.map(w => w.variant_id || w.product_variant_id).filter(Boolean);
      setWishlistIds(new Set(wIds));

    } catch (error) {
      toast.error("Failed to load catalog");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) {
      bootstrap();
      return;
    }

    setLoading(true);
    try {
      await ProductService.search(searchTerm).catch(() => {});
      const res = await ProductService.getFeed(searchTerm);
      
      setItems(getUniqueProducts(res?.data || res));
      setRecommended([]); 
      setTrending([]); 
      setActiveCategory("All");
    } catch {
      toast.error("Search failed");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleWishlist = async (e, variantId) => {
    e.preventDefault(); 
    e.stopPropagation();
    if (!variantId) return toast.error("This product is currently unavailable.");

    const isWishlisted = wishlistIds.has(variantId);
    setWishlistIds(prev => {
      const next = new Set(prev);
      if (isWishlisted) next.delete(variantId);
      else next.add(variantId);
      return next;
    });

    try {
      if (isWishlisted) {
        await UserService.removeFromWishlist(variantId);
        toast.success("Removed from wishlist");
      } else {
        await UserService.addToWishlist(variantId);
        toast.success("Added to wishlist ❤️");
      }
    } catch (error) {
      setWishlistIds(prev => {
        const next = new Set(prev);
        if (isWishlisted) next.add(variantId);
        else next.delete(variantId);
        return next;
      });
      toast.error("Failed to update wishlist");
    }
  };

  const handleAddToCart = async (e, variantId) => {
    e.preventDefault();
    e.stopPropagation();
    if (!variantId) {
      toast.error("Select a specific size/color on the product page to add to bag.");
      return false;
    }

    try {
      let activeSession = sessionId;
      if (!activeSession) {
        const res = await SessionService.start('web');
        activeSession = res?.data?.session_id || res?.session_id;
        setSessionId(activeSession);
      }
      await CartService.add(variantId, 1, activeSession);
      toast.success("Added to your bag! 🛍️");
      UserService.captureEvent('add_to_cart', 'product_variant', variantId).catch(() => {});
      return true;
    } catch (error) {
      toast.error("Could not add item to bag");
      return false;
    }
  };

  const visibleItems = activeCategory === "All"
    ? (items || [])
    : (items || []).filter(p => 
        p && p.category && typeof p.category === 'string' && 
        p.category.toLowerCase() === activeCategory.toLowerCase()
      );

  if (loading) {
    return (
      <div className="space-y-12 animate-pulse w-full max-w-[1600px] mx-auto px-4">
        <Skeleton className="h-20 w-full max-w-lg rounded-3xl" />
        <Skeleton className="h-14 w-full max-w-3xl rounded-full" />
        {/* Tighter Grid for Skeletons too */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5 gap-x-4 gap-y-10 sm:gap-x-6 sm:gap-y-12">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(i => <Skeleton key={i} className="aspect-[3/4] rounded-2xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-12 w-full max-w-[1600px] mx-auto pb-20 px-4 md:px-8 pt-4">

      {/* --- HEADER --- */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative flex flex-col xl:flex-row justify-between items-start xl:items-center gap-8 bg-gradient-to-br from-white to-zinc-50/50 p-8 md:p-10 rounded-[2rem] md:rounded-[2.5rem] border border-zinc-100 shadow-sm overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-zinc-100/50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />

        <div className="relative z-10">
          <h1 className="text-5xl md:text-7xl font-serif font-bold tracking-tighter text-zinc-900 drop-shadow-sm">
            Shop
          </h1>
          <p className="text-zinc-500 mt-3 md:mt-4 flex items-center gap-2 text-base md:text-lg">
            <Sparkles size={18} className="text-amber-500 animate-pulse" /> Curated exclusively for your Style DNA.
          </p>
        </div>

        <form onSubmit={handleSearch} className="relative w-full xl:w-[450px] z-10">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
          <Input
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search linen shirts, running shoes..."
            className="pl-14 py-7 rounded-full bg-white border border-zinc-200 focus-visible:ring-2 focus-visible:ring-black/5 focus-visible:border-zinc-400 transition-all text-base shadow-sm"
          />
          <AnimatePresence>
            {searchTerm && (
              <motion.button 
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                type="submit" 
                className="absolute right-2.5 top-1/2 -translate-y-1/2 bg-black text-white p-2.5 rounded-full hover:scale-105 hover:shadow-lg transition-all"
              >
                <ArrowRight size={18} />
              </motion.button>
            )}
          </AnimatePresence>
        </form>
      </motion.div>

      {/* --- CATEGORY FILTERS --- */}
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`
              whitespace-nowrap px-6 py-3 rounded-full font-bold transition-all duration-300 text-xs tracking-wide uppercase
              ${activeCategory === cat 
                ? "bg-zinc-900 text-white shadow-md scale-105" 
                : "bg-white text-zinc-500 border border-zinc-200 hover:border-zinc-400 hover:text-zinc-900 hover:bg-zinc-50"}
            `}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* --- RECOMMENDED SECTION --- */}
      <AnimatePresence>
        {recommended.length > 0 && activeCategory === "All" && !searchTerm && (
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-6"
          >
            <div className="flex items-center gap-3 border-b border-zinc-100 pb-4">
              <div className="bg-gradient-to-br from-amber-100 to-orange-100 p-2.5 rounded-xl text-amber-600 shadow-inner">
                <Sparkles size={20} />
              </div>
              <h2 className="text-2xl md:text-3xl font-serif font-bold tracking-tight text-zinc-900">Top Picks For You</h2>
            </div>
            {/* Tighter Grid! */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5 gap-x-4 gap-y-10 sm:gap-x-6 sm:gap-y-12">
              {recommended.slice(0, 5).map((item, i) => (
                <ProductCard key={`rec-${item.product_id}`} item={item} index={i} wishlistIds={wishlistIds} onWishlist={handleToggleWishlist} onAddToCart={handleAddToCart} />
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {/* --- TRENDING NOW SECTION --- */}
      <AnimatePresence>
        {trending.length > 0 && activeCategory === "All" && !searchTerm && (
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-6 pt-6"
          >
            <div className="flex items-center gap-3 border-b border-zinc-100 pb-4">
              <div className="bg-gradient-to-br from-red-100 to-rose-100 p-2.5 rounded-xl text-red-600 shadow-inner">
                <Flame size={20} />
              </div>
              <h2 className="text-2xl md:text-3xl font-serif font-bold tracking-tight text-zinc-900">Trending Now</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5 gap-x-4 gap-y-10 sm:gap-x-6 sm:gap-y-12">
              {trending.slice(0, 5).map((item, i) => (
                <ProductCard key={`trend-${item.product_id}`} item={item} index={i} wishlistIds={wishlistIds} onWishlist={handleToggleWishlist} onAddToCart={handleAddToCart} />
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {/* --- MAIN CATALOG --- */}
      <section className="space-y-6 pt-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between border-b border-zinc-100 pb-4 gap-2">
          <h2 className="text-2xl md:text-3xl font-serif font-bold tracking-tight text-zinc-900">
            {searchTerm ? `Results for "${searchTerm}"` : activeCategory !== "All" ? `${activeCategory} Collection` : "All Products"}
          </h2>
          <span className="text-zinc-400 font-bold text-xs uppercase tracking-widest">{visibleItems.length} items</span>
        </div>

        {visibleItems.length === 0 ? (
          <div className="py-20 flex flex-col items-center justify-center text-center bg-zinc-50 rounded-3xl border border-zinc-100">
            <Search size={40} className="text-zinc-300 mb-4" />
            <p className="text-zinc-500 text-base font-medium">No products found for this category.</p>
            {activeCategory !== "All" && (
              <button 
                onClick={() => setActiveCategory("All")}
                className="mt-6 px-6 py-2.5 bg-black text-white text-xs font-bold uppercase tracking-widest rounded-full hover:bg-zinc-800 transition-colors"
              >
                View all products
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5 gap-x-4 gap-y-10 sm:gap-x-6 sm:gap-y-12">
            {visibleItems.map((item, i) => (
              <ProductCard 
                key={`cat-${item.product_id || item.variant_id || i}`} 
                item={item} 
                index={i}
                wishlistIds={wishlistIds}
                onWishlist={handleToggleWishlist}
                onAddToCart={handleAddToCart}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

// ================= PREMIUM PRODUCT CARD =================
function ProductCard({ item, index, wishlistIds, onWishlist, onAddToCart }) {
  const [isAdding, setIsAdding] = useState(false);
  if (!item) return null;

  const variantId = item.variant_id || item.variants?.[0]?.variant_id || null;
  const price = item.final_price || item.base_price || item.variants?.[0]?.final_price || item.variants?.[0]?.base_price || 0;
  const originalPrice = item.base_price || item.variants?.[0]?.base_price || price;
  const hasDiscount = (item.discount_percent > 0) || (item.variants?.[0]?.discount_percent > 0);
  const discountAmount = item.discount_percent || item.variants?.[0]?.discount_percent || 0;
  
  const displayImage = item.image_url || item.image || item.images?.[0] || item.variants?.[0]?.images?.[0] || item.variants?.[0]?.image_url || "https://placehold.co/600x800/F8F9FA/a1a1aa?text=No+Image";
  const isWishlisted = variantId ? wishlistIds.has(variantId) : false;

  const handleQuickAdd = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsAdding(true);
    await onAddToCart(e, variantId);
    setIsAdding(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4, ease: "easeOut" }}
      className="group relative h-full flex flex-col"
    >
      <Link to={`/dash/product/${item.product_id || item.variant_id}`} className="block h-full flex flex-col">
        <Card className="border-none bg-transparent shadow-none h-full flex flex-col">
          
          {/* PREMIUM IMAGE CONTAINER CHANGES:
             1. rounded-xl: Sharper corners fit square images better.
             2. bg-white + border-zinc-100/50: Very subtle definition instead of a harsh gray border.
             3. Shadow on hover: Provides luxury lift.
          */}
          <div className="relative aspect-[4/5] bg-white rounded-xl overflow-hidden mb-4 border border-zinc-100/50 transition-all duration-500 group-hover:border-zinc-200/60 group-hover:shadow-[0_8px_24px_-12px_rgba(0,0,0,0.12)]">
            
            {hasDiscount && (
              <Badge className="absolute top-3 left-3 z-20 bg-zinc-900 text-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest shadow-sm border-none">
                {discountAmount}% OFF
              </Badge>
            )}

            {/* Kept p-1.5 for max size, but it looks better in the sharper container */}
            <img 
              src={displayImage} 
              alt={item.name || "Product"} 
              className="w-full h-full object-contain p-1.5 mix-blend-multiply group-hover:scale-105 transition-transform duration-700 ease-in-out" 
            />
            
            <button onClick={(e) => onWishlist(e, variantId)} className="absolute top-3 right-3 z-20 p-2 rounded-full bg-white/80 backdrop-blur-sm shadow-sm border border-white/40 text-zinc-400 hover:text-red-500 hover:scale-110 active:scale-95 transition-all duration-300">
              <Heart size={18} className={`transition-colors ${isWishlisted ? "fill-red-500 text-red-500" : ""}`} />
            </button>

            <div className="absolute bottom-3 left-3 right-3 translate-y-10 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 ease-out z-20 hidden md:block">
              <button onClick={handleQuickAdd} disabled={isAdding || !variantId} className="w-full py-3 bg-zinc-900/95 backdrop-blur-sm text-white rounded-lg font-bold tracking-wider text-xs flex items-center justify-center gap-2 hover:bg-black shadow-sm active:scale-95 transition-all disabled:opacity-80">
                {isAdding ? <Loader2 size={14} className="animate-spin" /> : <ShoppingBag size={14} />} 
                {isAdding ? "Adding..." : "QUICK ADD"}
              </button>
            </div>
          </div>

          <CardContent className="p-0 space-y-1.5 flex-1 px-0.5">
            <div className="text-[10px] uppercase tracking-[0.2em] text-zinc-400 font-bold">
              {item.brand || item.category || "Daksha"}
            </div>
            <h3 className="font-medium text-base text-zinc-900 leading-snug group-hover:underline decoration-1 underline-offset-4 transition-all line-clamp-2">
              {item.name || "Untitled Product"}
            </h3>
          </CardContent>

          <CardFooter className="p-0 pt-3 flex items-baseline gap-2 mt-auto px-0.5">
            <span className="font-serif text-lg font-bold text-black tracking-tight">₹{price}</span>
            {hasDiscount && <span className="text-xs font-medium text-zinc-400 line-through">₹{originalPrice}</span>}
          </CardFooter>

        </Card>
      </Link>
    </motion.div>
  );
}