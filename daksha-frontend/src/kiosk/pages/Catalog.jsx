import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, X, Loader2, SlidersHorizontal, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const CATEGORIES = ["All", "Shirts", "Pants", "Dresses", "Shoes", "Accessories", "Ethnic", "Sports"];

export default function KioskCatalog() {
  const navigate = useNavigate();
  const { resetIdleTimer } = useKiosk();
  const [products, setProducts]       = useState([]);
  const [loading, setLoading]         = useState(true);
  const [searchTerm, setSearchTerm]   = useState('');
  const [activeCategory, setActiveCategory] = useState('All');

  useEffect(() => {
    fetchProducts();
  }, [activeCategory]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = { limit: 60 };
      if (activeCategory !== 'All') params.category = activeCategory;
      const res = await api.get('/products', { params });
      setProducts(Array.isArray(res.data) ? res.data : []);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const filtered = products.filter(p => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      p.name?.toLowerCase().includes(q) ||
      p.brand?.toLowerCase().includes(q) ||
      p.color?.toLowerCase().includes(q)
    );
  });

  const handleProductClick = (item) => {
    resetIdleTimer();
    navigate(`/kiosk/product/${item.product_id}`);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] bg-slate-50">

      {/* ── Top bar: search + ask AI shortcut ─── */}
      <div className="bg-white border-b px-6 py-4 flex items-center gap-4 shadow-sm">
        <div className="relative flex-1 max-w-2xl">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 h-6 w-6 text-slate-400" />
          <Input
            className="h-16 pl-14 pr-12 text-xl rounded-2xl border-2 focus:border-slate-900"
            placeholder="Search products, brands…"
            value={searchTerm}
            onChange={(e) => { resetIdleTimer(); setSearchTerm(e.target.value); }}
          />
          {searchTerm && (
            <button type="button" className="absolute right-4 top-1/2 -translate-y-1/2 p-1"
              onClick={() => setSearchTerm('')}>
              <X className="h-5 w-5 text-slate-400" />
            </button>
          )}
        </div>

        <Button
          type="button"
          size="lg"
          className="h-16 px-8 text-lg gap-3 rounded-2xl bg-slate-900 hover:bg-slate-700 shrink-0"
          onClick={() => navigate('/kiosk/chat')}
        >
          <Sparkles className="w-6 h-6" />
          Ask Daksha AI
        </Button>
      </div>

      {/* ── Category chips ─── */}
      <div className="bg-white border-b px-6 py-3 flex gap-3 overflow-x-auto scrollbar-hide">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            type="button"
            onClick={() => { resetIdleTimer(); setActiveCategory(cat); }}
            className={`
              px-6 py-3 rounded-full text-lg font-medium whitespace-nowrap transition-all
              ${activeCategory === cat
                ? 'bg-slate-900 text-white shadow-md'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}
            `}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* ── Product grid ─── */}
      <div className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center gap-4">
            <Loader2 className="w-14 h-14 animate-spin text-slate-300" />
            <p className="text-xl text-slate-400">Loading catalog…</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="h-96 flex flex-col items-center justify-center gap-4 text-slate-400">
            <SlidersHorizontal className="w-16 h-16 opacity-20" />
            <p className="text-2xl">No products found</p>
            <Button type="button" variant="outline" size="lg" className="text-lg h-14 px-8 rounded-full"
              onClick={() => { setSearchTerm(''); setActiveCategory('All'); }}>
              Clear Filters
            </Button>
          </div>
        ) : (
          <AnimatePresence>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 pb-10">
              {filtered.map((item, i) => (
                <motion.div
                  key={item.variant_id || item.product_id || i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  onClick={() => handleProductClick(item)}
                  className="bg-white rounded-3xl overflow-hidden shadow-sm hover:shadow-xl cursor-pointer transition-all duration-300 active:scale-[0.97] group"
                >
                  <div className="aspect-[3/4] overflow-hidden bg-slate-100">
                    <img
                      src={item.image || 'https://via.placeholder.com/300x400'}
                      alt={item.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      loading="lazy"
                    />
                  </div>
                  <div className="p-4 space-y-1">
                    {item.brand && (
                      <p className="text-xs font-bold tracking-widest text-slate-400 uppercase">{item.brand}</p>
                    )}
                    <p className="text-base font-semibold text-slate-900 line-clamp-2 leading-snug">{item.name}</p>
                    {(item.color || item.size) && (
                      <p className="text-sm text-slate-400">{[item.color, item.size].filter(Boolean).join(' · ')}</p>
                    )}
                    <p className="text-xl font-bold text-slate-900 pt-1">
                      ₹{(item.final_price || item.base_price || 0).toLocaleString('en-IN')}
                      {item.discount_percent > 0 && (
                        <span className="ml-2 text-sm font-normal line-through text-slate-400">
                          ₹{(item.original_price || 0).toLocaleString('en-IN')}
                        </span>
                      )}
                    </p>
                    {item.discount_percent > 0 && (
                      <Badge className="bg-green-100 text-green-700 text-xs">
                        {item.discount_percent}% off
                      </Badge>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
