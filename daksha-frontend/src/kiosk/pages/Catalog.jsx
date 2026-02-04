import React, { useEffect, useState } from 'react';
import { useKiosk } from '../context/KioskSessionContext';
import { KioskService } from '@/lib/kioskApi';
import ProductCardLarge from '../components/ProductCardLarge';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Filter, X } from 'lucide-react';
import { Loader2 } from 'lucide-react';

export default function Catalog() {
  const { sessionActive, startSession } = useKiosk();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');

  // Hardcoded categories for Kiosk UI (Can be dynamic)
  const CATEGORIES = ["All", "Shoes", "Clothing", "Accessories", "Sports"];

  useEffect(() => {
    // Safety check: if accessed directly without session, start one
    if (!sessionActive) {
      startSession();
    }
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      // API: GET /products (with limit=50 for speed)
      const data = await KioskService.listProducts(50);
      setProducts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load catalog", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    // In a real app, trigger API search here
    // For now, client-side filtering for immediate feedback
  };

  const filteredProducts = products.filter(p => {
    const matchesCategory = activeCategory === 'All' || p.category === activeCategory;
    const matchesSearch = !searchTerm || 
      p.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
      p.brand?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]"> {/* Subtract header height */}
      
      {/* Filter Bar */}
      <div className="bg-white border-b px-8 py-4 flex gap-4 overflow-x-auto no-scrollbar">
        {CATEGORIES.map(cat => (
          <Button
            key={cat}
            variant={activeCategory === cat ? "default" : "outline"}
            size="lg"
            onClick={() => setActiveCategory(cat)}
            className="rounded-full px-8 text-lg h-14 whitespace-nowrap"
          >
            {cat}
          </Button>
        ))}
      </div>

      {/* Main Grid Area */}
      <div className="flex-1 overflow-y-auto p-8 bg-slate-50">
        
        {/* Search Bar */}
        <div className="mb-8 max-w-2xl mx-auto relative">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 h-8 w-8 text-slate-400" />
          <Input 
            className="h-20 pl-20 pr-8 text-2xl rounded-full shadow-sm border-2 focus:border-primary"
            placeholder="Search for products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button 
              className="absolute right-6 top-1/2 -translate-y-1/2 p-2 bg-slate-100 rounded-full"
              onClick={() => setSearchTerm('')}
            >
              <X className="h-6 w-6 text-slate-500" />
            </button>
          )}
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="w-16 h-16 animate-spin text-primary" />
            <p className="text-xl text-slate-500">Loading catalog...</p>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="h-96 flex flex-col items-center justify-center text-slate-400">
            <Filter className="w-24 h-24 mb-4 opacity-20" />
            <p className="text-2xl">No products found</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8 pb-20">
            {filteredProducts.map(product => (
              <ProductCardLarge key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
