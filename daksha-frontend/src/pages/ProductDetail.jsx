import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ProductService, CartService, UserService, SessionService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { 
  ShoppingBag, Heart, ChevronLeft, Star, 
  Truck, RefreshCcw, Sparkles, Loader2
} from "lucide-react";
import { toast } from "sonner";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  // --- Data State ---
  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState(null);
  const [wishlistIds, setWishlistIds] = useState(new Set());

  // --- Selections ---
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedSize, setSelectedSize] = useState("");
  const [activeImage, setActiveImage] = useState("");
  const [addingToCart, setAddingToCart] = useState(false);

  // ================= FETCH DATA =================
  useEffect(() => {
    const fetchProductData = async () => {
      setLoading(true);
      try {
        const [prodRes, simRes, wlRes, sessRes] = await Promise.all([
          ProductService.getDetail(id),
          ProductService.getSimilar(id).catch(() => ({ data: [] })),
          UserService.getWishlist().catch(() => ({ data: { items: [] } })),
          SessionService.getActive().catch(() => null)
        ]);

        const p = prodRes.data || prodRes;
        if (!p) throw new Error("Product not found");
        
        setProduct(p);
        setSimilar(Array.isArray(simRes?.data) ? simRes.data : []);
        setSessionId(sessRes?.data?.session_id || sessRes?.session_id || null);

        const wlItems = wlRes?.data?.items || wlRes?.items || [];
        setWishlistIds(new Set(wlItems.map(w => w.variant_id || w.product_variant_id).filter(Boolean)));

        // Safe Initialization: Handle both nested variants and flat products
        if (p.variants && p.variants.length > 0) {
          const firstVar = p.variants[0];
          setSelectedColor(firstVar.color || "");
          setSelectedSize(firstVar.size || "");
          setActiveImage(firstVar.images?.[0] || firstVar.image_url || p.image || "");
        }

        UserService.captureEvent('product_view', 'product', p.product_id).catch(() => {});

      } catch (e) {
        console.error("Detail Load Error:", e);
        toast.error("Failed to load product details.");
        navigate('/dash/shop');
      } finally {
        setLoading(false);
      }
    };

    fetchProductData();
  }, [id, navigate]);

  // ================= VARIANT LOGIC =================
  
  const availableColors = useMemo(() => {
    if (!product?.variants) return [];
    return [...new Set(product.variants.map(v => v.color).filter(Boolean))];
  }, [product]);

  const availableSizesForColor = useMemo(() => {
    if (!product?.variants) return [];
    // If colors exist, filter by selected color. Otherwise just show all sizes.
    const filtered = availableColors.length > 0 && selectedColor
      ? product.variants.filter(v => v.color === selectedColor)
      : product.variants;
    return [...new Set(filtered.map(v => v.size).filter(Boolean))];
  }, [product, selectedColor, availableColors]);

  // Bulletproof variant finder
  const currentVariant = useMemo(() => {
    if (!product) return null;
    if (!product.variants || product.variants.length === 0) return product; // Flat fallback

    return product.variants.find(v => {
      const matchColor = availableColors.length === 0 || v.color === selectedColor;
      const matchSize = availableSizesForColor.length === 0 || v.size === selectedSize;
      return matchColor && matchSize;
    }) || product.variants.find(v => v.color === selectedColor) || product.variants[0];
  }, [product, selectedColor, selectedSize, availableColors, availableSizesForColor]);

  useEffect(() => {
    const newImage = currentVariant?.images?.[0] || currentVariant?.image_url;
    if (newImage) setActiveImage(newImage);
  }, [currentVariant]);

  useEffect(() => {
    if (selectedColor && !availableSizesForColor.includes(selectedSize) && availableSizesForColor.length > 0) {
      setSelectedSize(availableSizesForColor[0]);
    }
  }, [selectedColor, availableSizesForColor, selectedSize]);


  // ================= ACTIONS =================
  
  const handleAddToCart = async () => {
    const variantId = currentVariant?.variant_id || product?.variant_id;
    
    if (!variantId) {
      return toast.error("Please select a specific size/color.");
    }
    
    setAddingToCart(true);
    try {
      // 1. Ensure we have a session ID before calling Cart API (Fixes 422 Error)
      let activeSession = sessionId;
      if (!activeSession) {
        const res = await SessionService.start('web');
        activeSession = res?.data?.session_id || res?.session_id;
        setSessionId(activeSession);
      }

      // 2. Add to cart with the exact variant_id
      await CartService.add(variantId, 1, activeSession);
      toast.success("Added to your bag! 🛍️");
      
      // 3. Log event
      UserService.captureEvent('add_to_cart', 'product_variant', variantId).catch(() => {});
    } catch (e) {
      console.error(e);
      toast.error("Could not add to cart. Please try again.");
    } finally {
      setAddingToCart(false);
    }
  };

  const isWishlisted = currentVariant ? wishlistIds.has(currentVariant.variant_id || product?.variant_id) : false;

  const handleToggleWishlist = async () => {
    const varId = currentVariant?.variant_id || product?.variant_id;
    if (!varId) return;
    
    setWishlistIds(prev => {
      const next = new Set(prev);
      if (isWishlisted) next.delete(varId);
      else next.add(varId);
      return next;
    });

    try {
      if (isWishlisted) {
        await UserService.removeFromWishlist(varId);
        toast.success("Removed from wishlist");
      } else {
        await UserService.addToWishlist(varId);
        toast.success("Added to wishlist ❤️");
      }
    } catch (error) {
      toast.error("Failed to update wishlist");
    }
  };

  // ================= RENDER =================

  if (loading) {
    return (
      <div className="w-full max-w-[1600px] mx-auto p-4 md:p-10 grid lg:grid-cols-12 gap-16 animate-pulse">
        <Skeleton className="lg:col-span-7 aspect-[4/5] rounded-[3rem]" />
        <div className="lg:col-span-5 space-y-8 pt-10">
          <Skeleton className="h-6 w-1/4 rounded-full" />
          <Skeleton className="h-20 w-full rounded-2xl" />
          <Skeleton className="h-12 w-1/3 rounded-xl" />
          <Skeleton className="h-40 w-full rounded-3xl" />
        </div>
      </div>
    );
  }

  if (!product) return null;

  // Safe variable extraction
  const price = currentVariant?.final_price || currentVariant?.base_price || product?.base_price || 0;
  const originalPrice = currentVariant?.base_price || product?.base_price || price;
  const hasDiscount = (currentVariant?.discount_percent > 0) || (product?.discount_percent > 0);
  const discountVal = currentVariant?.discount_percent || product?.discount_percent || 0;
  
  const defaultPlaceholder = "https://placehold.co/800x1000/F8F9FA/a1a1aa?text=No+Image";
  const images = currentVariant?.images?.length > 0 ? currentVariant.images : [product?.image || defaultPlaceholder];
  const displayImage = activeImage || images[0];

  return (
    <div className="w-full max-w-[1600px] mx-auto bg-white min-h-screen pb-32 pt-6 px-4 md:px-10">
      
      {/* Top Nav */}
      <div className="mb-10">
        <button onClick={() => navigate(-1)} className="group flex items-center text-sm font-semibold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors">
          <ChevronLeft size={18} className="mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Collection
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-24">
        
        {/* ================= LEFT: PREMIUM IMAGE GALLERY ================= */}
        <div className="lg:col-span-7 flex flex-col md:flex-row gap-6">
          
          {/* Thumbnails */}
          <div className="order-2 md:order-1 flex md:flex-col gap-4 overflow-x-auto md:overflow-y-auto scrollbar-hide md:w-28 shrink-0">
            {images.map((img, idx) => (
              <button 
                key={idx} 
                onClick={() => setActiveImage(img)}
                className={`relative aspect-[3/4] w-24 md:w-full rounded-2xl overflow-hidden border-[3px] transition-all bg-[#F8F9FA]
                  ${displayImage === img ? 'border-zinc-900 shadow-md' : 'border-transparent hover:border-zinc-300 opacity-60 hover:opacity-100'}`}
              >
                <img src={img} alt={`Thumbnail ${idx}`} className="w-full h-full object-contain mix-blend-multiply p-3" />
              </button>
            ))}
          </div>

          {/* Main Large Image */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="order-1 md:order-2 flex-1 relative bg-[#F8F9FA] rounded-[3rem] overflow-hidden aspect-[4/5] border border-zinc-100 shadow-[inset_0_0_50px_rgba(0,0,0,0.02)]"
          >
            {hasDiscount && (
              <Badge className="absolute top-8 left-8 z-20 bg-gradient-to-r from-red-600 to-rose-500 text-white px-5 py-2.5 text-xs font-bold uppercase tracking-[0.2em] shadow-xl border-none">
                {discountVal}% OFF
              </Badge>
            )}
            <AnimatePresence mode="wait">
              <motion.img
                key={displayImage}
                initial={{ opacity: 0, filter: 'blur(10px)' }}
                animate={{ opacity: 1, filter: 'blur(0px)' }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                src={displayImage}
                alt={product.name}
                className="w-full h-full object-contain mix-blend-multiply p-12 lg:p-20"
              />
            </AnimatePresence>
          </motion.div>
        </div>

        {/* ================= RIGHT: PRODUCT INFO ================= */}
        <div className="lg:col-span-5 flex flex-col lg:pt-8">
          
          {/* Brand & Title */}
          <div className="mb-8">
            <h3 className="text-xs font-bold uppercase tracking-[0.3em] text-zinc-400 mb-4 flex items-center gap-3">
              <span>{product.brand || "Exclusive"}</span>
              <span className="w-1.5 h-1.5 bg-zinc-300 rounded-full" />
              <span>{product.category || "Collection"}</span>
            </h3>
            
            <h1 className="text-5xl lg:text-6xl font-serif font-bold text-zinc-900 leading-[1.1] mb-6 tracking-tight">
              {product.name}
            </h1>
            
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-baseline gap-3">
                <span className="text-4xl font-serif font-bold tracking-tight text-black">₹{price}</span>
                {hasDiscount && <span className="text-xl font-medium text-zinc-400 line-through decoration-zinc-300">₹{originalPrice}</span>}
              </div>
              
              <div className="flex items-center gap-1.5 text-sm text-amber-600 bg-amber-50 px-4 py-1.5 rounded-full font-bold shadow-sm border border-amber-100">
                <Star size={16} className="fill-amber-500 text-amber-500" /> 4.9 <span className="text-amber-600/60 font-medium ml-1">(128 Reviews)</span>
              </div>
            </div>
          </div>

          <Separator className="my-8" />

          {/* Color Selector */}
          {availableColors.length > 0 && (
            <div className="mb-10">
              <div className="flex justify-between items-center mb-4">
                <span className="font-bold text-zinc-900 text-lg tracking-wide">Color</span>
                <span className="text-sm font-medium text-zinc-500 bg-zinc-100 px-3 py-1 rounded-full">{selectedColor}</span>
              </div>
              <div className="flex flex-wrap gap-4">
                {availableColors.map(color => (
                  <button
                    key={color}
                    onClick={() => setSelectedColor(color)}
                    className={`
                      px-6 py-3.5 rounded-full border-2 text-sm font-bold tracking-wide transition-all duration-300
                      ${selectedColor === color 
                        ? 'border-zinc-900 bg-zinc-900 text-white shadow-[0_8px_20px_rgba(0,0,0,0.15)] scale-105' 
                        : 'border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 hover:bg-zinc-50'}
                    `}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Size Selector */}
          {availableSizesForColor.length > 0 && (
            <div className="mb-12">
              <div className="flex justify-between items-center mb-4">
                <span className="font-bold text-zinc-900 text-lg tracking-wide">Select Size</span>
                <button className="text-sm font-bold text-zinc-400 hover:text-zinc-900 underline decoration-2 decoration-zinc-200 underline-offset-4 transition-colors">Size Guide</button>
              </div>
              <div className="grid grid-cols-4 md:grid-cols-5 gap-3">
                {availableSizesForColor.map(size => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`
                      h-16 rounded-2xl border-2 flex items-center justify-center font-bold transition-all duration-300 text-base uppercase
                      ${selectedSize === size 
                        ? 'border-zinc-900 bg-zinc-900 text-white shadow-[0_8px_20px_rgba(0,0,0,0.15)] scale-[1.03]' 
                        : 'border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 hover:bg-zinc-50'}
                    `}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4 mb-14">
            <Button 
              onClick={handleAddToCart} 
              disabled={addingToCart || (!currentVariant && !product?.variant_id)}
              className="flex-1 h-[4.5rem] rounded-full bg-zinc-900 hover:bg-black text-white text-lg font-bold tracking-wide shadow-[0_10px_40px_rgba(0,0,0,0.2)] transition-all active:scale-95 disabled:opacity-50 disabled:active:scale-100"
            >
              {addingToCart ? <Loader2 className="animate-spin mr-3" /> : <ShoppingBag className="mr-3" />} 
              {addingToCart ? "Adding..." : "Add to Bag"}
            </Button>
            
            <button 
              onClick={handleToggleWishlist}
              className={`h-[4.5rem] w-[4.5rem] flex shrink-0 items-center justify-center rounded-full border-2 transition-all duration-300 active:scale-95
                ${isWishlisted 
                  ? 'border-red-500 bg-red-50 shadow-[0_8px_20px_rgba(239,68,68,0.15)]' 
                  : 'border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50'}`}
            >
              <Heart size={28} className={isWishlisted ? 'fill-red-500 text-red-500' : 'text-zinc-400 hover:text-zinc-600 transition-colors'} />
            </button>
          </div>

          {/* Description & Trust Details */}
          <div className="space-y-8 bg-zinc-50 p-8 rounded-[2rem] border border-zinc-100">
            <div>
              <h3 className="font-serif font-bold text-2xl text-zinc-900 mb-3 flex items-center gap-3">
                <Sparkles size={20} className="text-amber-500" /> The Details
              </h3>
              <p className="text-zinc-500 leading-relaxed text-base font-medium">
                {product.description || "A masterpiece of modern design. Crafted with exceptional attention to detail, balancing aesthetic elegance with everyday utility."}
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-6 pt-6 border-t border-zinc-200/60">
              <div>
                <p className="text-xs uppercase font-bold tracking-[0.15em] text-zinc-400 mb-1.5">Material</p>
                <p className="text-base font-bold text-zinc-900">{product.fabric_type || "Premium Blend"}</p>
              </div>
              <div>
                <p className="text-xs uppercase font-bold tracking-[0.15em] text-zinc-400 mb-1.5">Occasion</p>
                <p className="text-base font-bold text-zinc-900">{product.occasion || "Versatile"}</p>
              </div>
            </div>

            {/* Trust Badges */}
            <div className="flex flex-col gap-4 pt-6 border-t border-zinc-200/60">
              <div className="flex items-center gap-4 text-sm font-semibold text-zinc-700">
                <div className="bg-white p-2.5 rounded-xl shadow-sm border border-zinc-100"><Truck size={20} className="text-zinc-900" /></div>
                Complimentary standard delivery.
              </div>
              <div className="flex items-center gap-4 text-sm font-semibold text-zinc-700">
                <div className="bg-white p-2.5 rounded-xl shadow-sm border border-zinc-100"><RefreshCcw size={20} className="text-zinc-900" /></div>
                Seamless 14-day returns & exchanges.
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}