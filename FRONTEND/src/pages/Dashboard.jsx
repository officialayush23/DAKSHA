// src/pages/Dashboard.jsx
import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/apiClient";
import { Bot, Store, ShoppingBag, Package, LifeBuoy, ShoppingCart, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { motion, AnimatePresence } from "framer-motion";
import { trackProductView } from "@/lib/analytics"; // fire-and-forget utils

// ---------- Hooks ----------
function useScrollDirection() {
  const [visible, setVisible] = useState(true);
  const lastY = useRef(0);
  useEffect(() => {
    function onScroll() {
      const y = window.scrollY;
      if (y > lastY.current && y > 80) setVisible(false);
      else setVisible(true);
      lastY.current = y;
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return visible;
}

// ---------- Shared/Skeleton ----------
function ProductSkeletonCard() {
  return (
    <div className="space-y-2">
      <div className="h-52 w-full rounded-xl bg-slate-800 animate-pulse" />
      <div className="h-4 w-3/4 bg-slate-800 rounded animate-pulse" />
      <div className="h-3 w-1/3 bg-slate-800 rounded animate-pulse" />
    </div>
  );
}

// ---------- Dashboard ----------
export default function Dashboard() {
  const { user, profile } = useAuth();
  const navigate = useNavigate();
  const [picked, setPicked] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const headerVisible = useScrollDirection();

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        setLoading(true);
        const [a, b] = await Promise.allSettled([
          api.get("/recommendations/home?limit=8"),
          api.get("/recommendations/trending?limit=8"),
        ]);
        if (!mounted) return;
        if (a.status === "fulfilled") setPicked(a.value.data.items || []);
        if (b.status === "fulfilled") setTrending(b.value.data.items || []);
      } catch (e) {
        console.error("Dashboard load error", e);
      } finally {
        setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, [user]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <motion.header
        initial={{ y: 0 }}
        animate={{ y: headerVisible ? 0 : -84 }}
        transition={{ type: "tween", duration: 0.22 }}
        className="fixed top-0 left-0 right-0 z-50 backdrop-blur px-4 bg-black/60 border-b border-white/5"
      >
        <div className="max-w-6xl mx-auto h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white/5 p-2 rounded-md">
              <Store className="h-5 w-5 text-white" />
            </div>
            <div className="font-semibold">Daksha</div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate("/cart")}>
              <ShoppingCart className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => navigate("/profile")}>
              <div className="h-8 w-8 rounded-full bg-white/6 flex items-center justify-center text-xs">U</div>
            </Button>
          </div>
        </div>
      </motion.header>

      <main className="pt-20 pb-16 max-w-6xl mx-auto px-4 space-y-10">
        {/* Hero */}
        <section className="rounded-2xl p-8 bg-gradient-to-r from-gray-900 to-gray-800 border border-white/5">
          <div className="flex flex-col md:flex-row md:justify-between gap-6">
            <div>
              <Badge variant="outline" className="mb-3">AI-Powered Picks</Badge>
              <h1 className="text-4xl font-bold">
                {getGreeting()}, {profile?.full_name?.split(" ")[0] || "Guest"}
              </h1>
              <p className="text-slate-400 mt-2">We curated outfits & products you’re likely to love.</p>
              <div className="mt-4 flex gap-3">
                <Button size="lg" onClick={() => navigate("/products")}>Start Shopping</Button>
                <Button size="lg" variant="outline" onClick={() => navigate("/chat")}><Bot className="mr-2" />Ask Agent</Button>
              </div>
            </div>
            <div className="hidden md:block w-60 h-48 rounded-xl bg-white/5 flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl font-bold">Smart</div>
                <div className="text-slate-400">Recommendations</div>
              </div>
            </div>
          </div>
        </section>

        {/* Picked for you */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-semibold">Picked for you</h2>
              <p className="text-slate-400 text-sm">Personalized by Daksha AI</p>
            </div>
            <div>
              <Button variant="link" onClick={() => navigate("/products")}>See all</Button>
            </div>
          </div>

          <div className="relative">
            {loading ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Array(4).fill(0).map((_, i) => <ProductSkeletonCard key={i} />)}
              </div>
            ) : picked.length ? (
              <div className="flex gap-4 overflow-x-auto pb-2">
                {picked.map(p => (
                  <motion.div key={p.id || p.product_id} whileHover={{ scale: 1.02 }} className="min-w-[200px] w-[200px]">
                    <ProductCard product={p} />
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center border border-dashed border-white/5 rounded-xl">
                <p className="text-slate-400">No personalized picks yet — start browsing!</p>
                <Button className="mt-4" onClick={() => navigate("/products")}>Browse</Button>
              </div>
            )}
          </div>
        </section>

        {/* Trending */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">Trending now</h2>
          </div>

          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array(4).fill(0).map((_, i) => <ProductSkeletonCard key={i} />)}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {trending.map(p => <ProductCard key={p.product_id || p.id} product={p} />)}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

// ---------- Product Card ----------
function ProductCard({ product }) {
  const navigate = useNavigate();
  const [openReason, setOpenReason] = useState(false);

  const onClick = () => {
    try {
      trackProductView({ id: product.id || product.product_id, name: product.name });
    } catch (e) { /* swallow */ }
    navigate(`/products/${product.id || product.product_id}`);
  };

  const img = product.image_url || (product.product_variants && product.product_variants[0]?.image_url);

  return (
    <div className="bg-white/3 rounded-xl p-3 cursor-pointer" >
      <div className="relative" onClick={onClick}>
        <div className="aspect-[3/4] rounded-lg overflow-hidden bg-slate-900">
          {img ? <img src={img} className="h-full w-full object-cover" alt={product.name} /> : <div className="h-full w-full flex items-center justify-center text-slate-600">No Image</div>}
        </div>

        {product.similarity !== undefined && (
          <div className="absolute top-2 left-2 bg-black/70 text-xs px-2 py-1 rounded">
            {Math.round((product.similarity || 0) * 100)}% match
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="flex justify-between items-start gap-2">
          <div>
            <div className="font-medium line-clamp-1">{product.name}</div>
            <div className="text-sm text-slate-400">₹{product.base_price}</div>
          </div>
          <div className="text-right">
            <button className="text-xs text-slate-300" onClick={() => setOpenReason(v => !v)}>{openReason ? "Hide" : "Why?"}</button>
          </div>
        </div>

        <AnimatePresence>
          {openReason && product.agent_reason && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="mt-2 text-xs text-slate-300 bg-white/2 rounded p-2">
              {product.agent_reason}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
