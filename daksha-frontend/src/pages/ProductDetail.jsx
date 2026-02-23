import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ProductService, CartService, UserService, SessionService, RecommendationService } from "../lib/api";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

import { 
  ShoppingBag, Heart, ChevronLeft, Star, 
  Truck, Loader2, Send, Sparkles
} from "lucide-react";
import { toast } from "sonner";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  // --- Data State ---
  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [boughtTogether, setBoughtTogether] = useState([]);
  const [reviews, setReviews] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState(null);
  const [wishlistIds, setWishlistIds] = useState(new Set());

  // --- Selections ---
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedSize, setSelectedSize] = useState("");
  const [activeImage, setActiveImage] = useState("");
  const [addingToCart, setAddingToCart] = useState(false);

  // --- Review Form ---
  const [reviewText, setReviewText] = useState("");
  const [reviewRating, setReviewRating] = useState(5);
  const [submittingReview, setSubmittingReview] = useState(false);

  // ================= FETCH DATA =================
  useEffect(() => {
    const fetchProductData = async () => {
      setLoading(true);
      try {
        const [prodRes, simRes, boughtRes, revRes, wlRes, sessRes] = await Promise.all([
          ProductService.getDetail(id),
          RecommendationService.getSimilarVariants(id).catch(() => ({ data: [] })),
          RecommendationService.getBoughtTogether(id).catch(() => ({ data: [] })),
          ProductService.getReviews(id).catch(() => ({ data: [] })),
          UserService.getWishlist().catch(() => ({ data: { items: [] } })),
          SessionService.getActive().catch(() => null)
        ]);

        const p = prodRes.data || prodRes;
        if (!p) throw new Error("Product not found");
        
        setProduct(p);
        setSimilar(Array.isArray(simRes?.data) ? simRes.data : simRes || []);
        setBoughtTogether(Array.isArray(boughtRes?.data) ? boughtRes.data : boughtRes || []);
        setReviews(Array.isArray(revRes?.data) ? revRes.data : revRes || []);
        
        setSessionId(sessRes?.data?.session_id || sessRes?.session_id || null);

        const wlItems = wlRes?.data?.items || wlRes?.items || [];
        setWishlistIds(new Set(wlItems.map(w => w.variant_id || w.product_variant_id).filter(Boolean)));

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
    const filtered = availableColors.length > 0 && selectedColor
      ? product.variants.filter(v => v.color === selectedColor)
      : product.variants;
    return [...new Set(filtered.map(v => v.size).filter(Boolean))];
  }, [product, selectedColor, availableColors]);

  const currentVariant = useMemo(() => {
    if (!product) return null;
    if (!product.variants || product.variants.length === 0) return product;

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
  
  const handleAddToCart = async (variantIdToUse = null) => {
    const variantId = variantIdToUse || currentVariant?.variant_id || product?.variant_id;
    
    if (!variantId) {
      return toast.error("Please select a specific size/color.");
    }
    
    setAddingToCart(true);
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
    } catch (e) {
      toast.error("Could not add to cart. Please try again.");
    } finally {
      setAddingToCart(false);
    }
  };

  const isWishlisted = currentVariant ? wishlistIds.has(currentVariant.variant_id || product?.variant_id) : false;

  const handleToggleWishlist = async (varIdToUse = null) => {
    const varId = varIdToUse || currentVariant?.variant_id || product?.variant_id;
    if (!varId) return;
    
    const currentlyWishlisted = wishlistIds.has(varId);

    setWishlistIds(prev => {
      const next = new Set(prev);
      if (currentlyWishlisted) next.delete(varId);
      else next.add(varId);
      return next;
    });

    try {
      if (currentlyWishlisted) {
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

  const submitReview = async (e) => {
    e.preventDefault();
    if (!reviewText.trim()) return;
    setSubmittingReview(true);
    try {
      await ProductService.addReview({
        product_id: product.product_id,
        rating: reviewRating,
        comment: reviewText
      });
      toast.success("Review posted!");
      setReviewText("");
      
      const revRes = await ProductService.getReviews(product.product_id);
      setReviews(Array.isArray(revRes?.data) ? revRes.data : revRes || []);
    } catch (error) {
      toast.error("Failed to post review");
    } finally {
      setSubmittingReview(false);
    }
  };

  // ================= RENDER =================

  if (loading) {
    return (
      <div className="w-full max-w-[1300px] mx-auto p-4 md:p-8 grid lg:grid-cols-2 gap-10 animate-pulse">
        <Skeleton className="aspect-[4/5] rounded-[2rem]" />
        <div className="space-y-6 pt-4">
          <Skeleton className="h-6 w-1/4 rounded-full" />
          <Skeleton className="h-12 w-3/4 rounded-xl" />
          <Skeleton className="h-8 w-1/3 rounded-xl" />
          <Skeleton className="h-40 w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (!product) return null;

  const price = currentVariant?.final_price || currentVariant?.base_price || product?.base_price || 0;
  const originalPrice = currentVariant?.base_price || product?.base_price || price;
  const hasDiscount = (currentVariant?.discount_percent > 0) || (product?.discount_percent > 0);
  const discountVal = currentVariant?.discount_percent || product?.discount_percent || 0;
  
  const defaultPlaceholder = "https://placehold.co/800x1000/F8F9FA/a1a1aa?text=No+Image";
  const images = currentVariant?.images?.length > 0 ? currentVariant.images : [product?.image || defaultPlaceholder];
  const displayImage = activeImage || images[0];

  const avgRating = reviews.length ? (reviews.reduce((a, b) => a + b.rating, 0) / reviews.length).toFixed(1) : "New";

  return (
    <div className="w-full max-w-[1300px] mx-auto bg-white min-h-screen pb-20 pt-4 px-4 md:px-8">
      
      {/* Top Nav */}
      <div className="mb-6">
        <button onClick={() => navigate(-1)} className="group flex items-center text-xs font-bold uppercase tracking-widest text-zinc-400 hover:text-black transition-colors">
          <ChevronLeft size={16} className="mr-1.5 group-hover:-translate-x-1 transition-transform" /> Back to Shop
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 mb-16 relative">
        
        {/* ================= LEFT: COMPACT IMAGE GALLERY ================= */}
        {/* Changed layout to be sticky and properly sized */}
        <div className="lg:col-span-7 flex flex-col-reverse md:flex-row gap-4 lg:sticky lg:top-24 h-fit">
          <div className="flex md:flex-col gap-3 overflow-x-auto md:overflow-y-auto scrollbar-hide w-full md:w-20 shrink-0">
            {images.map((img, idx) => (
              <button 
                key={idx} 
                onClick={() => setActiveImage(img)}
                className={`relative aspect-[3/4] w-20 md:w-full rounded-xl overflow-hidden border-2 transition-all bg-[#F8F9FA] shrink-0
                  ${displayImage === img ? 'border-zinc-900 shadow-sm' : 'border-transparent hover:border-zinc-300 opacity-60 hover:opacity-100'}`}
              >
                <img src={img} alt={`Thumbnail ${idx}`} className="w-full h-full object-contain mix-blend-multiply p-2" />
              </button>
            ))}
          </div>

          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex-1 relative bg-[#F8F9FA] rounded-[2rem] overflow-hidden aspect-square md:aspect-[4/5] max-h-[650px] border border-zinc-100 flex items-center justify-center"
          >
            {hasDiscount && (
              <Badge className="absolute top-6 left-6 z-20 bg-gradient-to-r from-red-600 to-rose-500 text-white px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest shadow-md border-none">
                {discountVal}% OFF
              </Badge>
            )}
            <AnimatePresence mode="wait">
              <motion.img
                key={displayImage}
                initial={{ opacity: 0, filter: 'blur(5px)' }}
                animate={{ opacity: 1, filter: 'blur(0px)' }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                src={displayImage}
                alt={product.name}
                // Drastically reduced padding here from p-20 to p-8
                className="w-full h-full object-contain mix-blend-multiply p-8 md:p-12"
              />
            </AnimatePresence>
          </motion.div>
        </div>

        {/* ================= RIGHT: PRODUCT INFO ================= */}
        {/* Adjusted typography and button heights to standard comfortable sizes */}
        <div className="lg:col-span-5 flex flex-col">
          
          <div className="mb-6">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-3 flex items-center gap-2">
              <span>{product.brand || "Exclusive"}</span>
              <span className="w-1 h-1 bg-zinc-300 rounded-full" />
              <span>{product.category || "Collection"}</span>
            </h3>
            
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-zinc-900 leading-tight mb-4 tracking-tight">
              {product.name}
            </h1>
            
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-black">₹{price}</span>
                {hasDiscount && <span className="text-base font-medium text-zinc-400 line-through decoration-zinc-300">₹{originalPrice}</span>}
              </div>
              
              <div className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-3 py-1 rounded-full font-bold border border-amber-100">
                <Star size={12} className="fill-amber-500 text-amber-500" /> {avgRating} <span className="text-amber-600/60 font-medium ml-1">({reviews.length})</span>
              </div>
            </div>
          </div>

          <Separator className="my-6" />

          {/* Color Selector */}
          {availableColors.length > 0 && (
            <div className="mb-8">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-bold text-zinc-900 tracking-wide">Color</span>
                <span className="text-xs font-medium text-zinc-500 bg-zinc-100 px-2.5 py-0.5 rounded-full">{selectedColor}</span>
              </div>
              <div className="flex flex-wrap gap-2.5">
                {availableColors.map(color => (
                  <button
                    key={color}
                    onClick={() => setSelectedColor(color)}
                    className={`
                      px-5 py-2.5 rounded-full border-2 text-xs font-bold tracking-wide transition-all duration-300
                      ${selectedColor === color 
                        ? 'border-zinc-900 bg-zinc-900 text-white shadow-md' 
                        : 'border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400'}
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
            <div className="mb-8">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-bold text-zinc-900 tracking-wide">Select Size</span>
              </div>
              <div className="grid grid-cols-4 sm:grid-cols-5 gap-2">
                {availableSizesForColor.map(size => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`
                      h-12 rounded-xl border-2 flex items-center justify-center font-bold transition-all duration-300 text-sm uppercase
                      ${selectedSize === size 
                        ? 'border-zinc-900 bg-zinc-900 text-white shadow-md' 
                        : 'border-zinc-200 bg-white text-zinc-600 hover:border-zinc-400'}
                    `}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Actions - Height reduced from 72px to 56px */}
          <div className="flex gap-3 mb-10">
            <Button 
              onClick={() => handleAddToCart()} 
              disabled={addingToCart || (!currentVariant && !product?.variant_id)}
              className="flex-1 h-14 rounded-full bg-zinc-900 hover:bg-black text-white text-sm font-bold tracking-wide shadow-lg transition-all active:scale-95 disabled:opacity-50"
            >
              {addingToCart ? <Loader2 className="animate-spin mr-2 h-4 w-4" /> : <ShoppingBag className="mr-2 h-4 w-4" />} 
              {addingToCart ? "Adding..." : "Add to Bag"}
            </Button>
            
            <button 
              onClick={() => handleToggleWishlist()}
              className={`h-14 w-14 flex shrink-0 items-center justify-center rounded-full border-2 transition-all duration-300 active:scale-95
                ${isWishlisted ? 'border-red-500 bg-red-50 shadow-md' : 'border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50'}`}
            >
              <Heart size={20} className={isWishlisted ? 'fill-red-500 text-red-500' : 'text-zinc-400'} />
            </button>
          </div>

          {/* Details Box */}
          <div className="space-y-6 bg-zinc-50/50 p-6 rounded-3xl border border-zinc-100">
            <div>
              <h3 className="font-serif font-bold text-lg text-zinc-900 mb-2 flex items-center gap-2">
                <Sparkles size={16} className="text-amber-500" /> The Details
              </h3>
              <p className="text-zinc-600 leading-relaxed text-sm font-medium">
                {product.description || "A masterpiece of modern design. Crafted with exceptional attention to detail."}
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-zinc-200/60">
              <div>
                <p className="text-[10px] uppercase font-bold tracking-widest text-zinc-400 mb-1">Material</p>
                <p className="text-sm font-bold text-zinc-900">{product.fabric_type || "Premium Blend"}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase font-bold tracking-widest text-zinc-400 mb-1">Occasion</p>
                <p className="text-sm font-bold text-zinc-900">{product.occasion || "Versatile"}</p>
              </div>
            </div>
            <div className="flex flex-col gap-3 pt-4 border-t border-zinc-200/60">
              <div className="flex items-center gap-3 text-xs font-semibold text-zinc-700">
                <div className="bg-white p-2 rounded-lg shadow-sm border border-zinc-100"><Truck size={14} className="text-zinc-900" /></div>
                Complimentary standard delivery.
              </div>
            </div>
          </div>

        </div>
      </div>

      <Separator className="my-12" />

      {/* ================= RECOMMENDATIONS & REVIEWS ================= */}
      
      {boughtTogether.length > 0 && (
        <section className="mb-16">
          <h2 className="text-2xl font-serif font-bold tracking-tight text-zinc-900 mb-6">Frequently Bought Together</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
            {boughtTogether.map((item) => (
              <MiniProductCard 
                key={item.variant_id} item={item} 
                wishlisted={wishlistIds.has(item.variant_id)}
                onWishlist={() => handleToggleWishlist(item.variant_id)}
                onAddToCart={(e) => { e.preventDefault(); handleAddToCart(item.variant_id); }}
              />
            ))}
          </div>
        </section>
      )}

      {similar.length > 0 && (
        <section className="mb-16">
          <h2 className="text-2xl font-serif font-bold tracking-tight text-zinc-900 mb-6">You Might Also Like</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
            {similar.map((item) => (
              <MiniProductCard 
                key={item.variant_id} item={item} 
                wishlisted={wishlistIds.has(item.variant_id)}
                onWishlist={() => handleToggleWishlist(item.variant_id)}
                onAddToCart={(e) => { e.preventDefault(); handleAddToCart(item.variant_id); }}
              />
            ))}
          </div>
        </section>
      )}

      {/* Reviews */}
      <section className="max-w-3xl mx-auto">
        <h2 className="text-2xl font-serif font-bold tracking-tight text-zinc-900 mb-6 text-center">Customer Reviews</h2>
        
        <div className="bg-zinc-50 p-5 rounded-[1.5rem] border border-zinc-100 mb-8">
          <h4 className="font-bold mb-3 text-sm">Write a Review</h4>
          <form onSubmit={submitReview} className="space-y-3">
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star 
                  key={star} size={20} 
                  onClick={() => setReviewRating(star)}
                  className={`cursor-pointer transition-colors ${star <= reviewRating ? 'fill-amber-500 text-amber-500' : 'text-zinc-300'}`} 
                />
              ))}
            </div>
            <Textarea 
              placeholder="What did you think about this product?" 
              value={reviewText} onChange={e => setReviewText(e.target.value)}
              className="bg-white border-zinc-200 text-sm min-h-[80px]"
            />
            <Button type="submit" disabled={submittingReview} className="rounded-full h-10 px-6 text-xs">
              {submittingReview ? <Loader2 className="animate-spin mr-2 h-3 w-3" /> : <Send className="mr-2 h-3 w-3" />} Post Review
            </Button>
          </form>
        </div>

        <div className="space-y-5">
          {reviews.length === 0 ? (
            <p className="text-center text-zinc-500 py-8 text-sm">No reviews yet. Be the first to review!</p>
          ) : (
            reviews.map((rev) => (
              <div key={rev.id} className="border-b border-zinc-100 pb-5">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-zinc-900 text-sm">{rev.user_name}</span>
                  <span className="text-[10px] text-zinc-400">{new Date(rev.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex mb-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Star key={star} size={12} className={star <= rev.rating ? 'fill-amber-500 text-amber-500' : 'text-zinc-200'} />
                  ))}
                </div>
                <p className="text-zinc-600 text-xs leading-relaxed">{rev.comment}</p>
              </div>
            ))
          )}
        </div>
      </section>

    </div>
  );
}

// INCLUDED FIX: Using item.images?.[0] for the MiniProductCard
function MiniProductCard({ item, wishlisted, onWishlist, onAddToCart }) {
  const price = item.final_price || item.base_price || 0;
  const originalPrice = item.base_price || price;
  const hasDiscount = item.discount_percent > 0 || originalPrice > price;
  
  const displayImage = item.images?.[0] || item.image_url || item.image || "https://placehold.co/400x500/F8F9FA/a1a1aa?text=No+Image";
  
  return (
    <Link to={`/dash/product/${item.product_id || item.variant_id}`} className="group block">
      <Card className="border-none shadow-none bg-transparent h-full flex flex-col">
        <div className="relative aspect-[4/5] bg-[#F8F9FA] rounded-2xl overflow-hidden mb-3 transition-all duration-500 group-hover:shadow-md">
          <img 
            src={displayImage} 
            alt={item.name || "Product Image"} 
            className="w-full h-full object-contain p-3 mix-blend-multiply group-hover:scale-105 transition-transform duration-700" 
          />
          <button 
            onClick={(e) => { e.preventDefault(); onWishlist(); }}
            className="absolute top-2 right-2 p-1.5 rounded-full bg-white/90 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all hover:scale-110"
          >
            <Heart size={14} className={wishlisted ? 'fill-red-500 text-red-500' : 'text-zinc-400'} />
          </button>
          <button 
            onClick={onAddToCart}
            className="absolute bottom-2 left-2 right-2 py-2 bg-black/90 text-white text-[10px] uppercase tracking-wider font-bold rounded-lg opacity-0 group-hover:opacity-100 translate-y-2 group-hover:translate-y-0 transition-all shadow-md"
          >
            + Quick Add
          </button>
        </div>
        <div className="px-1 flex flex-col flex-1">
          <h4 className="text-xs font-bold text-zinc-900 line-clamp-1">{item.name || "Recommended Item"}</h4>
          <div className="flex items-center gap-1.5 mt-auto pt-1">
            <span className="font-bold text-xs">₹{price}</span>
            {hasDiscount && <span className="text-[10px] text-zinc-400 line-through">₹{originalPrice}</span>}
          </div>
        </div>
      </Card>
    </Link>
  );
}