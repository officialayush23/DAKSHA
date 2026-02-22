import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ProductService, CartService, UserService, SessionService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

import { 
  Search, Loader2, Sparkles, Filter, 
  Heart, ShoppingBag, ArrowRight 
} from "lucide-react";
import { toast } from "sonner";

const CATEGORIES = ["All", "Shoes", "Clothing", "Accessories", "Home", "Sports"];

// Helper function to ensure we only show ONE variant per Product on the Shop page
const getUniqueProducts = (items) => {
  if (!Array.isArray(items)) return [];
  const uniqueMap = new Map();
  
  items.forEach(item => {
    // Group by product_id so we don't show the same shirt 5 times for different sizes
    if (item && item.product_id && !uniqueMap.has(item.product_id)) {
      uniqueMap.set(item.product_id, item);
    }
  });
  
  return Array.from(uniqueMap.values());
};

export default function ShopPage() {
  // --- Data State ---
  const [recommended, setRecommended] = useState([]);
  const [items, setItems] = useState([]);
  const [wishlistIds, setWishlistIds] = useState(new Set());
  const [sessionId, setSessionId] = useState(null);
  
  // --- UI State ---
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  // ================= LOAD DATA =================
  useEffect(() => {
    bootstrap();
  }, []);

  const bootstrap = async () => {
    setLoading(true);
    try {
      const sessRes = await SessionService.getActive().catch(() => null);
      const activeSessionId = sessRes?.data?.session_id || sessRes?.session_id || null;
      setSessionId(activeSessionId);

      const [feedRes, listRes, wlRes] = await Promise.all([
        ProductService.getFeed().catch(() => ({ data: [] })),
        ProductService.listProducts({ limit: 100 }).catch(() => ({ data: [] })),
        UserService.getWishlist().catch(() => ({ data: { items: [] } }))
      ]);

      // Apply the unique filter here
      setRecommended(getUniqueProducts(feedRes?.data || feedRes));
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

  // ================= ACTIONS =================
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

  // --- CRASH-PROOF FILTER LOGIC ---
  const visibleItems = activeCategory === "All"
    ? (items || [])
    : (items || []).filter(p => 
        p && p.category && typeof p.category === 'string' && 
        p.category.toLowerCase() === activeCategory.toLowerCase()
      );

  // ================= RENDER =================
  if (loading) {
    return (
      <div className="space-y-12 animate-pulse w-full max-w-[1600px] mx-auto">
        <Skeleton className="h-20 w-full max-w-lg rounded-3xl" />
        <Skeleton className="h-14 w-full max-w-3xl rounded-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-x-8 gap-y-12">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(i => <Skeleton key={i} className="aspect-[4/5] rounded-[2rem]" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-16 w-full max-w-[1600px] mx-auto pb-20">

      {/* --- HEADER --- */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative flex flex-col xl:flex-row justify-between items-start xl:items-center gap-8 bg-gradient-to-br from-white to-zinc-50/50 p-10 rounded-[2.5rem] border border-white shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-zinc-100/50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />

        <div className="relative z-10">
          <h1 className="text-6xl md:text-7xl font-serif font-bold tracking-tighter text-zinc-900 drop-shadow-sm">
            Shop
          </h1>
          <p className="text-zinc-500 mt-4 flex items-center gap-2 text-lg">
            <Sparkles size={18} className="text-amber-500 animate-pulse" /> Curated exclusively for your Style DNA.
          </p>
        </div>

        <form onSubmit={handleSearch} className="relative w-full xl:w-[500px] z-10">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
          <Input
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search linen shirts, running shoes..."
            className="pl-16 py-8 rounded-full bg-white/80 backdrop-blur-md border border-zinc-200/50 focus-visible:ring-4 focus-visible:ring-black/5 focus-visible:border-zinc-400 transition-all text-lg shadow-sm"
          />
          <AnimatePresence>
            {searchTerm && (
              <motion.button 
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                type="submit" 
                className="absolute right-3 top-1/2 -translate-y-1/2 bg-black text-white p-3.5 rounded-full hover:scale-105 hover:shadow-lg hover:shadow-black/20 transition-all"
              >
                <ArrowRight size={20} />
              </motion.button>
            )}
          </AnimatePresence>
        </form>
      </motion.div>

      {/* --- CATEGORY FILTERS --- */}
      <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide px-2">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`
              whitespace-nowrap px-8 py-3.5 rounded-full font-medium transition-all duration-500 text-sm tracking-wide
              ${activeCategory === cat 
                ? "bg-zinc-900 text-white shadow-xl shadow-zinc-900/20 scale-105" 
                : "bg-white text-zinc-500 border border-zinc-200/80 hover:border-zinc-400 hover:text-zinc-900 hover:bg-zinc-50"}
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
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-8"
          >
            <div className="flex items-center gap-4 border-b border-zinc-100 pb-6 px-2">
              <div className="bg-gradient-to-br from-amber-100 to-orange-100 p-3 rounded-2xl text-amber-600 shadow-inner">
                <Sparkles size={24} />
              </div>
              <h2 className="text-3xl font-serif font-bold tracking-tight text-zinc-900">Top Picks For You</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-x-8 gap-y-14">
              {recommended.map((item, i) => (
                <ProductCard 
                  key={item.product_id} 
                  item={item} 
                  index={i}
                  wishlistIds={wishlistIds}
                  onWishlist={handleToggleWishlist}
                  onAddToCart={handleAddToCart}
                />
              ))}
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {/* --- MAIN CATALOG --- */}
      <section className="space-y-8">
        <div className="flex items-center justify-between border-b border-zinc-100 pb-6 px-2">
          <h2 className="text-3xl font-serif font-bold tracking-tight text-zinc-900">
            {searchTerm ? `Results for "${searchTerm}"` : activeCategory !== "All" ? `${activeCategory} Collection` : "All Products"}
          </h2>
          <span className="text-zinc-400 font-medium text-sm">{visibleItems.length} items</span>
        </div>

        {visibleItems.length === 0 ? (
          <div className="py-20 flex flex-col items-center justify-center text-center">
            <p className="text-zinc-400 text-lg font-medium">No products found for this category yet.</p>
            {activeCategory !== "All" && (
              <button 
                onClick={() => setActiveCategory("All")}
                className="mt-4 text-black font-semibold underline decoration-2 underline-offset-4 hover:text-zinc-600"
              >
                View all products
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-x-8 gap-y-14">
            {visibleItems.map((item, i) => (
              <ProductCard 
                key={item.product_id || item.variant_id || i} 
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


/* ========================================================= */
/* PRODUCT CARD (CRASH-PROOF DATA EXTRACTION)                */
/* ========================================================= */

function ProductCard({ item, index, wishlistIds, onWishlist, onAddToCart }) {
  const [isAdding, setIsAdding] = useState(false);

  // --- BULLETPROOF EXTRACTION LOGIC ---
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
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.5, ease: "easeOut" }}
      className="group relative h-full flex flex-col"
    >
      <Link to={`/dash/product/${item.product_id || item.variant_id}`} className="block h-full flex flex-col">
        <Card className="border-none bg-transparent shadow-none h-full flex flex-col">
          
          {/* --- PREMIUM IMAGE CONTAINER --- */}
          <div className="relative aspect-[4/5] bg-[#F8F9FA] rounded-[2rem] overflow-hidden mb-6 flex items-center justify-center transition-all duration-700 group-hover:bg-[#F0F2F5] group-hover:shadow-[0_20px_40px_-15px_rgba(0,0,0,0.1)]">
            
            {hasDiscount && (
              <Badge className="absolute top-5 left-5 z-20 bg-gradient-to-r from-red-600 to-rose-500 text-white px-3.5 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] shadow-lg border-none">
                {discountAmount}% OFF
              </Badge>
            )}

            <img
              src={displayImage}
              alt={item.name || "Product"}
              className="w-full h-full object-contain p-10 mix-blend-multiply group-hover:scale-105 transition-transform duration-[1.5s] ease-out"
            />

            {/* --- HOVER ACTIONS --- */}
            <button 
              onClick={(e) => onWishlist(e, variantId)}
              className="absolute top-5 right-5 z-20 p-3.5 rounded-full bg-white/90 backdrop-blur-md shadow-[0_4px_20px_rgba(0,0,0,0.08)] border border-white text-zinc-400 hover:text-red-500 hover:scale-110 active:scale-95 transition-all duration-300"
            >
              <Heart 
                size={20} 
                className={`transition-colors ${isWishlisted ? "fill-red-500 text-red-500" : ""}`} 
              />
            </button>

            <div className="absolute bottom-5 left-5 right-5 translate-y-10 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-500 ease-out z-20">
              <button 
                onClick={handleQuickAdd}
                disabled={isAdding || !variantId}
                className="w-full py-4 bg-black/90 backdrop-blur-2xl text-white rounded-2xl font-semibold tracking-wide text-sm flex items-center justify-center gap-2 hover:bg-black shadow-[0_10px_30px_rgba(0,0,0,0.2)] active:scale-95 transition-all disabled:opacity-80"
              >
                {isAdding ? <Loader2 size={18} className="animate-spin" /> : <ShoppingBag size={18} />} 
                {isAdding ? "Adding..." : "Quick Add"}
              </button>
            </div>
            
          </div>

          {/* --- CONTENT DETAILS --- */}
          <CardContent className="p-0 space-y-2.5 flex-1 px-1">
            <div className="flex justify-between items-center">
              <div className="text-[11px] uppercase tracking-[0.25em] text-zinc-400 font-bold">
                {item.brand || item.category || "Daksha"}
              </div>
            </div>

            <h3 className="font-medium text-xl text-zinc-900 leading-snug group-hover:text-zinc-600 transition-colors line-clamp-2 pr-4">
              {item.name || "Untitled Product"}
            </h3>
          </CardContent>

          {/* --- FOOTER / PRICING --- */}
          <CardFooter className="p-0 pt-4 flex items-baseline gap-2.5 mt-auto px-1">
            <span className="font-serif text-2xl font-bold text-black tracking-tight">
              ₹{price}
            </span>
            {hasDiscount && (
              <span className="text-sm font-medium text-zinc-400 line-through">
                ₹{originalPrice}
              </span>
            )}
          </CardFooter>
          
        </Card>
      </Link>
    </motion.div>
  );
}