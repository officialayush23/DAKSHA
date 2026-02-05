import React, { useState, useEffect } from 'react';
import { ProductService } from '../lib/api';
import { Link } from 'react-router-dom';
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Search, Loader2, Sparkles, Filter } from 'lucide-react';
import { toast } from 'sonner';

export default function ShopPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');

  const CATEGORIES = ["All", "Shoes", "Clothing", "Accessories", "Home"];

  useEffect(() => {
    loadFeed();
  }, []);

  const loadFeed = async (intent = null) => {
    setLoading(true);
    try {
      const data = await ProductService.getFeed(intent);

      // 🔒 HARD GUARD — backend may return object on error
      setProducts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Feed error", error);
      toast.error("Failed to load products");
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) {
      loadFeed();
      return;
    }

    setLoading(true);
    try {
      // 1. Log search intent
      await ProductService.search(searchTerm);

      // 2. Fetch ranked feed
      await loadFeed(searchTerm);
    } catch (error) {
      toast.error("Search failed");
    } finally {
      setLoading(false);
    }
  };

  const displayedProducts =
    activeCategory === 'All'
      ? products
      : products.filter(
          (p) => p.category === activeCategory
        );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-serif font-bold">The Collection</h1>
          <p className="text-zinc-500 mt-2">
            Curated for you based on your unique style.
          </p>
        </div>

        <form onSubmit={handleSearch} className="relative w-full md:w-96 group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5 group-focus-within:text-black transition-colors" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search for 'linen shirts'..."
            className="pl-12 py-6 rounded-full bg-white border-zinc-200 shadow-sm focus:ring-1 focus:ring-black transition-all"
          />
        </form>
      </div>

      {/* Categories */}
      <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`
              px-6 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap border
              ${
                activeCategory === cat
                  ? 'bg-black text-white border-black'
                  : 'bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400'
              }
            `}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="h-96 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-zinc-300" />
        </div>
      ) : displayedProducts.length === 0 ? (
        <div className="h-64 flex flex-col items-center justify-center text-zinc-400">
          <Filter className="w-12 h-12 mb-4 opacity-20" />
          <p>No products found matching your criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {displayedProducts.map((product) => (
            <Link
              key={product.variant_id || product.product_id}
              to={`/dash/product/${product.product_id}`}
              className="group block"
            >
              <Card className="border-none shadow-none bg-transparent overflow-hidden">
                <div className="relative aspect-[3/4] bg-zinc-100 rounded-xl overflow-hidden mb-4">
                  <img
                    src={product.image || "https://placehold.co/600x800"}
                    alt={product.name || product.brand}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                  {product.scores?.trend > 0.8 && (
                    <div className="absolute top-3 left-3 bg-white/90 backdrop-blur px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                      <Sparkles size={10} className="text-amber-500" />
                      Trending
                    </div>
                  )}
                </div>

                <CardContent className="p-0 space-y-1">
                  <div className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                    {product.brand}
                  </div>
                  <h3 className="font-medium text-lg leading-tight group-hover:underline decoration-1 underline-offset-4">
                    {product.name || "Luxury Item"}
                  </h3>
                </CardContent>

                <CardFooter className="p-0 mt-2 flex items-center justify-between">
                  <span className="text-zinc-900 font-serif text-lg">
                    ₹{product.price}
                  </span>
                  {product.offer && (
                    <span className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded font-medium">
                      {product.offer.label}
                    </span>
                  )}
                </CardFooter>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
