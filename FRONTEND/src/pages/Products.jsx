// src/pages/ProductsPage.jsx
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient"; 
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  Search, Filter, ShoppingCart, Heart, Eye, 
  LayoutGrid, List as ListIcon, Loader2, ArrowLeft,
  X, ShoppingBag, ChevronDown, SlidersHorizontal
} from "lucide-react";
import { 
  trackProductView, 
  trackProductClick, 
  trackAddToCart, 
  flush, 
  trackEvent 
} from "@/lib/analytics";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default function ProductsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  
  // Data State
  const [allProducts, setAllProducts] = useState([]); 
  const [displayedProducts, setDisplayedProducts] = useState([]);
  
  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [priceRange, setPriceRange] = useState([0, 20000]);
  const [selectedGenders, setSelectedGenders] = useState([]);
  const [sortOption, setSortOption] = useState("newest");
  const [viewMode, setViewMode] = useState("grid");
  const [addingId, setAddingId] = useState(null);
  const [visibleCount, setVisibleCount] = useState(12);

  // -----------------------------
  // PAGE ENTER / EXIT TRACKING
  // -----------------------------
  useEffect(() => {
    trackEvent("page_enter", { page: "products_page" });
    return () => trackEvent("page_exit", { page: "products_page" });
  }, []);

  // --- 1. Fetch Data ---
  const fetchCatalog = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase
        .from('products')
        .select(`
          id, name, description, base_price, gender, style_tags, created_at,
          category:categories(name),
          variants:product_variants(id, image_url, price_override)
        `)
        .eq('is_active', true)
        .order('created_at', { ascending: false });

      if (error) throw error;

      const formatted = (data || []).map(p => {
        const variants = p.variants || [];
        const firstVariant = variants.length > 0 ? variants[0] : null;
        
        return {
          id: p.id,
          name: p.name,
          description: p.description,
          price: Number(p.base_price),
          gender: p.gender,
          category_name: p.category?.name || "General",
          image_url: firstVariant?.image_url || null,
          default_variant_id: firstVariant?.id || null, 
          tags: p.style_tags || [],
          created_at: p.created_at,
          has_stock: variants.length > 0
        };
      });

      setAllProducts(formatted);
      setDisplayedProducts(formatted);
    } catch (err) {
      console.error("Fetch error:", err);
      toast.error("Could not load products.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  // --- 2. Filters ---
  useEffect(() => {
    let result = [...allProducts];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(p => 
        p.name.toLowerCase().includes(q) || 
        p.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    result = result.filter(p => p.price >= priceRange[0] && p.price <= priceRange[1]);

    if (selectedGenders.length > 0) {
      result = result.filter(p => selectedGenders.includes(p.gender));
    }

    if (sortOption === "price_low") result.sort((a, b) => a.price - b.price);
    else if (sortOption === "price_high") result.sort((a, b) => b.price - a.price);
    else if (sortOption === "newest") result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    setDisplayedProducts(result);
  }, [allProducts, searchQuery, priceRange, selectedGenders, sortOption]);

  // --- 3. Add to Cart (with tracking) ---
  const handleAddToCart = async (product) => {
    if (!product.default_variant_id) return toast.error("Out of stock");

    setAddingId(product.id);

    try {
      // Use backend API - no direct Supabase writes
      const payload = {
        variant_id: product.default_variant_id,
        quantity: 1,
        fulfillment_location_id: "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" // Default location - should be configurable
      };

      await api.post("/cart", payload);
      toast.success(`Added ${product.name}`);
      trackAddToCart(product, 1, { source: "api" });
      await flush();
    } catch (err) {
      console.error("Failed to add to cart:", err);
      if (err.response?.status === 401) {
        toast.error("Please log in to add items to cart");
      } else {
        toast.error("Failed to add to cart");
      }
      trackEvent("add_to_cart_failed", { product_id: product.id, reason: String(err) });
    } finally {
      setAddingId(null);
    }
  };

  // ------------------------
  // FILTER TRACKING HERE
  // ------------------------
  const toggleGender = (g) => {
    setSelectedGenders(prev => {
      const newList = prev.includes(g)
        ? prev.filter(x => x !== g)
        : [...prev, g];

      trackEvent("filter_change", { genders: newList });

      return newList;
    });
  };

  return (
    <div className="min-h-screen dark:bg-background text-slate-100 font-sans ">
      
      {/* --- Sticky Glass Header --- */}
      <div className="sticky top-0 z-40 w-full border-b dark:bg-background backdrop-blur-xl">
        <div className="container max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          
          {/* Left: Brand & Back */}
          <div className="flex items-center gap-4 shrink-0">
            <Button 
              variant="ghost" 
              size="icon" 
              className="rounded-full hover:bg-white/10 text-slate-400 hover:text-white" 
              onClick={() => navigate("/home")}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <span className="font-bold text-lg tracking-tight hidden md:block text-slate-100">Store</span>
          </div>

          {/* Middle: Search */}
          <div className="flex-1 max-w-md relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 group-focus-within:text-white transition-colors" />
            <Input 
              placeholder="Search products..." 
              className="pl-10 h-10 rounded-full bg-slate-900 border-white/5 focus:bg-slate-800 focus:border-white/20 transition-all placeholder:text-slate-600 text-slate-200"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                trackEvent("search", { query: e.target.value });
              }}
            />
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center bg-slate-900/50 rounded-full p-1 border border-white/5">
               <button 
                 onClick={() => setViewMode("grid")} 
                 className={`p-2 rounded-full transition-all ${viewMode === 'grid' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
               >
                 <LayoutGrid className="h-4 w-4" />
               </button>
               <button 
                 onClick={() => setViewMode("list")} 
                 className={`p-2 rounded-full transition-all ${viewMode === 'list' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
               >
                 <ListIcon className="h-4 w-4" />
               </button>
            </div>
            
            <Sheet>
              <SheetTrigger asChild>
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="md:hidden rounded-full border-white/10 bg-transparent hover:bg-white/5 text-slate-300"
                >
                  <Filter className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-[300px] border-r-white/10 p-2 dark:bg-background text-slate-100">
                <SheetHeader className="text-left mb-6">
                  <SheetTitle className="text-white">Filters</SheetTitle>
                </SheetHeader>
                <FilterSidebar 
                  priceRange={priceRange} 
                  setPriceRange={(val) => {
                    setPriceRange(val);
                    trackEvent("filter_change", { price_range: val });
                  }}
                  selectedGenders={selectedGenders} 
                  toggleGender={toggleGender} 
                />
              </SheetContent>
            </Sheet>

            <Button 
              className="rounded-full relative bg-white text-slate-950 hover:bg-slate-200 font-semibold" 
              onClick={() => navigate("/cart")}
            >
              <ShoppingBag className="h-4 w-4 mr-2" /> 
              Cart
            </Button>
          </div>
        </div>
      </div>

      {/* --- Main Layout --- */}
      <div className="container max-w-7xl mx-auto px-4 py-8 flex items-start gap-10">
        
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block w-64 sticky top-24 shrink-0 space-y-8">
           <FilterSidebar 
             priceRange={priceRange} 
             setPriceRange={(val) => {
               setPriceRange(val);
               trackEvent("filter_change", { price_range: val });
             }}
             selectedGenders={selectedGenders} 
             toggleGender={toggleGender} 
             reset={() => { 
                setSelectedGenders([]); 
                setPriceRange([0, 20000]);
                trackEvent("filter_change", { reset: true });
             }}
           />
        </aside>

        {/* Content Area */}
        <main className="flex-1 min-h-[80vh]">
          
          {/* Header & Sort */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
             <div className="flex items-center gap-3">
               <h2 className="text-xl font-semibold tracking-tight text-white">All Products</h2>
               <Badge 
                 variant="secondary" 
                 className="bg-slate-900 text-slate-400 hover:bg-slate-900 border border-white/5"
               >
                 {displayedProducts.length}
               </Badge>
             </div>
             
             {/* Sort Select */}
             <Select 
               value={sortOption} 
               onValueChange={(v) => {
                 setSortOption(v);
                 trackEvent("sort_change", { option: v });
               }}
             >
               <SelectTrigger className="w-[160px] h-9 rounded-lg bg-slate-900 border-white/10 text-slate-300 focus:ring-0">
                 <span className="text-slate-500 mr-2">Sort by:</span> 
                 <SelectValue />
               </SelectTrigger>
               <SelectContent className="dark:bg-background border-white/10 text-slate-300">
                 <SelectItem value="relevance">Relevance</SelectItem>
                 <SelectItem value="newest">Newest Arrivals</SelectItem>
                 <SelectItem value="price_low">Price: Low to High</SelectItem>
                 <SelectItem value="price_high">Price: High to Low</SelectItem>
               </SelectContent>
             </Select>
          </div>

          {/* Active Filter Chips */}
          {(selectedGenders.length > 0 || priceRange[0] > 0 || priceRange[1] < 20000) && (
            <div className="flex flex-wrap gap-2 mb-6">
              {selectedGenders.map(g => (
                <Badge 
                  key={g} 
                  className="pl-3 pr-1.5 py-1 capitalize gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/5"
                >
                  {g} 
                  <X 
                    className="h-3 w-3 cursor-pointer hover:text-white" 
                    onClick={() => toggleGender(g)} 
                  />
                </Badge>
              ))}
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-6 px-2 text-xs text-slate-500 hover:text-white" 
                onClick={() => { 
                  setSelectedGenders([]); 
                  setPriceRange([0, 20000]); 
                  trackEvent("filter_change", { clear_all: true });
                }}
              >
                Clear all
              </Button>
            </div>
          )}

          {/* Grid */}
          {loading ? (
            <ProductGridSkeleton viewMode={viewMode} />
          ) : displayedProducts.length === 0 ? (
             <div className="flex flex-col items-center justify-center py-32 text-center border border-dashed border-white/5 rounded-3xl bg-white/[0.02]">
                <div className="bg-background p-4 rounded-full mb-4">
                  <Search className="h-8 w-8 text-slate-600" />
                </div>
                <h3 className="text-lg font-medium text-white">No products found</h3>
                <p className="text-slate-500 max-w-xs mx-auto mt-1 mb-6">
                  Try adjusting your price range or filters.
                </p>
                <Button 
                  variant="outline" 
                  className="border-white/10 text-white hover:bg-white/5" 
                  onClick={() => { 
                    setSearchQuery(""); 
                    setSelectedGenders([]); 
                    trackEvent("filter_change", { reset: true });
                  }}
                >
                  Clear Filters
                </Button>
             </div>
          ) : (
            <>
              <div className={
                viewMode === 'grid' 
                ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-8" 
                : "flex flex-col gap-4"
              }>
                {displayedProducts.slice(0, visibleCount).map((product) => (
                  <ProductTile 
                    key={product.id} 
                    product={product} 
                    viewMode={viewMode} 
                    onAdd={handleAddToCart} 
                    isAdding={addingId === product.id}
                    navigate={navigate}
                  />
                ))}
              </div>
              
              {/* Load More Button */}
              {visibleCount < displayedProducts.length && (
                <div className="mt-12 flex justify-center">
                  <Button 
                    variant="outline" 
                    size="lg" 
                    className="min-w-[200px] border-white/10 hover:bg-white/5 text-slate-300 bg-slate-900/50" 
                    onClick={() => setVisibleCount(prev => prev + 8)}
                  >
                    Load More Products
                  </Button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

// --- Sidebar ---
const FilterSidebar = ({ priceRange, setPriceRange, selectedGenders, toggleGender, reset }) => (
  <div className="space-y-8 animate-in slide-in-from-left-4 duration-500">
    <div>
      <div className="flex items-center justify-between mb-4">
         <h3 className="font-semibold text-sm tracking-wide text-white">Price Range</h3>
         {reset && (
           <button 
             onClick={reset} 
             className="text-[10px] text-slate-500 hover:text-white uppercase font-bold tracking-wider"
           >
             Reset
           </button>
         )}
      </div>

      <Card className="bg-background dark:bg-background p-4">
        <Slider 
          defaultValue={[0, 20000]} 
          max={20000} 
          step={100} 
          value={priceRange} 
          onValueChange={(val) => {
            setPriceRange(val);
            trackEvent("filter_change", { price_range: val });
          }} 
          className="my-4" 
        />
        <div className="flex justify-between text-xs font-mono text-slate-400">
          <span>₹{priceRange[0]}</span>
          <span>₹{priceRange[1]}</span>
        </div>
      </Card>
    </div>
    
    <div>
      <h3 className="font-semibold text-sm tracking-wide text-white mb-4">Department</h3>
      <div className="space-y-2">
         {['men', 'women', 'unisex', 'kids'].map(g => (
           <label 
             key={g} 
             className="flex items-center justify-between group cursor-pointer p-2 rounded-lg hover:bg-white/5 transition-colors"
           >
             <span className="text-sm capitalize text-slate-400 group-hover:text-slate-200">{g}</span>
             <Checkbox 
                checked={selectedGenders.includes(g)} 
                onCheckedChange={() => toggleGender(g)} 
                className="border-white/10 data-[state=checked]:bg-white data-[state=checked]:text-black" 
             />
           </label>
         ))}
      </div>
    </div>
  </div>
);

// --- PRODUCT TILE ---
function ProductTile({ product, viewMode, onAdd, isAdding, navigate }) {
  const isList = viewMode === 'list';
  const [liked, setLiked] = useState(false);
  const ref = useRef(null);

  // Intersection observer -> view tracking
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let viewed = false;

    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!viewed && entry.isIntersecting && entry.intersectionRatio > 0.5) {
          viewed = true;
          trackProductView(product);
        }
      });
    }, { threshold: [0.5] });

    io.observe(el);
    return () => io.disconnect();
  }, [product]);

  // Click handler -> product_click
  const handleClick = (e) => {
    if (e.target.closest('button')) return;
    trackProductClick(product);
    flush();
    navigate(`/products/${product.id}`);
  };

  return (
    <div 
      ref={ref} 
      onClick={handleClick} 
      className={`group relative flex ${isList ? 'flex-row items-center border border-white/5 bg-slate-900/40 p-4 rounded-xl' : 'flex-col gap-3 cursor-pointer'}`}
    >
      
      {/* IMAGE */}
      <div 
        className={`relative overflow-hidden rounded-xl bg-slate-900 border border-white/5 ${isList ? 'w-24 h-24 shrink-0' : 'aspect-square w-full'}`}
      >
        {product.image_url ? (
          <img 
            src={product.image_url} 
            alt={product.name} 
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" 
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-700">
            <SlidersHorizontal className="h-8 w-8 mb-2 opacity-50" />
          </div>
        )}
        
        {/* Like + preview buttons */}
        {!isList && (
          <div className="absolute top-2 right-2 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
             <button 
               onClick={(e) => { e.stopPropagation(); setLiked(!liked); }} 
               className="p-2 rounded-full bg-slate-950/80 backdrop-blur text-white hover:bg-white hover:text-black transition-colors border border-white/10"
             >
                <Heart className={`h-4 w-4 ${liked ? 'fill-current text-red-500 hover:text-red-500' : ''}`} />
             </button>

             <button 
               onClick={(e) => { 
                 e.stopPropagation(); 
                 trackEvent('quick_preview', { product_id: product.id }); 
               }} 
               className="p-2 rounded-full bg-slate-950/80 backdrop-blur text-white hover:bg-white hover:text-black transition-colors border border-white/10"
             >
                <Eye className="h-4 w-4" />
             </button>
          </div>
        )}

        {/* Tag */}
        <div className="absolute top-2 left-2">
           {product.tags?.slice(0, 1).map(tag => (
             <span 
               key={tag} 
               className="text-[10px] font-bold px-2 py-1 rounded bg-white text-black shadow-lg uppercase tracking-wider"
             >
               {tag}
             </span>
           ))}
        </div>
      </div>

      {/* DETAILS */}
      <div className={`flex flex-col ${isList ? 'ml-6 flex-1' : ''}`}>
        <div className="mb-1 flex justify-between items-start">
           <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
             {product.category_name}
           </span>
           {!product.has_stock && (
             <span className="text-[10px] text-red-500 font-bold uppercase">
               Sold Out
             </span>
           )}
        </div>
        
        <h3 className="text-sm font-medium text-slate-200 leading-tight group-hover:text-white transition-colors line-clamp-1 mb-1">
          {product.name}
        </h3>

        {isList && (
          <p className="text-sm text-slate-500 line-clamp-2 mb-3 max-w-lg">
            {product.description}
          </p>
        )}
        
        <div className="flex items-center justify-between mt-1">
           <span className="text-base font-semibold text-white">
             ₹{product.price.toLocaleString()}
           </span>
           
           <Button 
             size="sm"
             className={`h-8 rounded-full px-4 text-xs font-semibold transition-all ${isList ? '' : 'w-auto'}`}
             onClick={(e) => { e.stopPropagation(); onAdd(product); }} 
             disabled={isAdding || !product.has_stock}
             variant={!product.has_stock ? "ghost" : "secondary"}
           >
             {isAdding ? (
               <Loader2 className="h-3 w-3 animate-spin" />
             ) : (
               !product.has_stock ? "Unavailable" : "Add"
             )}
           </Button>
        </div>
      </div>
    </div>
  );
}

// --- Skeletons ---
const ProductGridSkeleton = ({ viewMode }) => (
  <div className={viewMode === 'grid' ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" : "space-y-4"}>
     {Array.from({ length: 8 }).map((_, i) => (
        viewMode === 'grid' ? (
          <div key={i} className="space-y-3">
             <Skeleton className="aspect-square w-full rounded-xl bg-slate-900" />
             <div className="space-y-2">
               <Skeleton className="h-4 w-2/3 bg-slate-900" />
               <Skeleton className="h-4 w-1/3 bg-slate-900" />
             </div>
          </div>
        ) : (
          <div 
            key={i} 
            className="flex gap-4 h-24 border border-slate-900 rounded-xl p-3"
          >
            <Skeleton className="w-24 h-full rounded-lg bg-slate-900" />
            <div className="flex-1 py-2 space-y-2">
              <Skeleton className="h-4 w-32 bg-slate-900" />
              <Skeleton className="h-4 w-1/2 bg-slate-900" />
            </div>
          </div>
        )
     ))}
  </div>
);
