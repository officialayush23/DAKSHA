// src/pages/ShopPage.jsx
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Filter, Search, Sparkles, Heart, ShoppingBag } from 'lucide-react';
import { ProductService, CartService } from '../lib/api';
import { toast } from 'sonner';
import { Input } from "@/components/ui/input"; // Shadcn Input

export default function ShopPage() {
  const [products, setProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  // 1. Load Initial Feed
  useEffect(() => {
    loadFeed();
  }, []);

  const loadFeed = async (filters = {}) => {
    setLoading(true);
    try {
      const res = await ProductService.getFeed(filters);
      setProducts(res.data);
    } catch (err) {
      toast.error("Collection unavailable");
    } finally {
      setLoading(false);
    }
  };

  // 2. Intent-Based Search
  const handleSearch = async (e) => {
    if (e.key === 'Enter') {
      try {
        setLoading(true);
        // This hits /user/search which logs intent + updates preferences
        await ProductService.search(searchQuery); 
        // Then we fetch the feed again, possibly filtered by the backend's understanding
        // For now, let's just do a basic text search filter on the client or re-fetch with query
        // Ideally, your /products API supports a 'q' param, or you use the recommendation feed
        const res = await ProductService.getFeed({ category: searchQuery }); // Simple mapping for now
        setProducts(res.data);
        toast.success(`Personalizing for "${searchQuery}"`);
      } catch (err) {
        toast.error("Search failed");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleAddToCart = async (e, variantId) => {
    e.preventDefault();
    try {
      await CartService.add(variantId, 1);
      toast.success("Added to Bag");
    } catch (err) {
      toast.error("Login required");
    }
  };

  return (
    <div className="space-y-12">
      {/* Header & Search */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-6">
        <div>
          <h1 className="text-5xl font-serif tracking-tighter mb-2">The Collection</h1>
          <p className="text-xs uppercase tracking-[0.2em] text-gray-400">Curated by Daksha AI</p>
        </div>
        
        <div className="relative w-full md:w-96">
          <Search className="absolute left-4 top-3.5 text-gray-400 w-4 h-4" />
          <Input 
            className="pl-12 rounded-full border-gray-200 bg-gray-50 h-12 font-serif placeholder:font-sans placeholder:text-xs placeholder:uppercase placeholder:tracking-wider focus-visible:ring-black"
            placeholder="Search for 'Wedding' or 'Office'..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearch}
          />
        </div>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[1,2,3,4].map(i => <div key={i} className="aspect-[3/4] bg-gray-100 rounded-sm animate-pulse" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-12">
          {products.map((p) => (
            <Link to={`/dash/product/${p.product_id}`} key={p.variant_id} className="group block cursor-pointer">
              <div className="aspect-[3/4] bg-gray-100 relative overflow-hidden rounded-sm mb-4">
                <img 
                  src={p.image || "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&q=80"} 
                  alt={p.name || p.brand}
                  className="w-full h-full object-cover bw-image group-hover:scale-105 transition-transform duration-700" 
                />
                
                {/* AI Reasoning Badge (Mock logic based on scores) */}
                {p.score > 0.8 && (
                  <div className="absolute top-3 right-3 bg-white/90 backdrop-blur px-3 py-1 flex items-center gap-1 shadow-sm">
                    <Sparkles size={10} className="text-emerald-500" />
                    <span className="text-[10px] font-bold uppercase tracking-wide">Best Match</span>
                  </div>
                )}

                {/* Quick Add Overlay */}
                <button 
                  onClick={(e) => handleAddToCart(e, p.variant_id)}
                  className="absolute inset-x-4 bottom-4 bg-white text-black py-3 text-[10px] uppercase font-bold tracking-widest translate-y-full opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 hover:bg-black hover:text-white shadow-xl"
                >
                  Add to Bag
                </button>
              </div>

              <div>
                <h3 className="font-serif text-lg leading-tight group-hover:underline decoration-gray-300 underline-offset-4">
                  {p.name || p.description}
                </h3>
                <div className="flex justify-between items-center mt-2 border-t border-gray-100 pt-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">{p.brand}</span>
                  <span className="font-medium text-sm">₹{p.price}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}