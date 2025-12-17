// src/components/product/ProductCardCompact.jsx
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Info, ShoppingCart, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import api from "@/lib/apiClient";
import {
  trackProductView,
  trackProductClick,
  trackAddToCart,
} from "@/lib/analytics";

export default function ProductCardCompact({ product, railId }) {
  const navigate = useNavigate();
  const ref = useRef(null);
  const [adding, setAdding] = useState(false);

  // ---- impression tracking (Unchanged Logic)
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let fired = false;
    const io = new IntersectionObserver(
      ([e]) => {
        if (!fired && e.isIntersecting) {
          fired = true;
          trackProductView({
            id: product.id,
            source: railId,
            price: product.price,
          });
        }
      },
      { threshold: 0.6 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [product, railId]);

  async function handleAdd(e) {
    e.stopPropagation();
    if (!product.default_variant_id) return;
    setAdding(true);
    try {
      await api.post("/cart/add", {
        variant_id: product.default_variant_id,
        quantity: 1,
      });
      trackAddToCart(product, 1, { source: railId });
    } finally {
      setAdding(false);
    }
  }

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      whileHover={{ y: -8 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      onClick={() => {
        trackProductClick({ id: product.id, source: railId });
        navigate(`/products/${product.id}`);
      }}
      className="group cursor-pointer min-w-[260px] md:min-w-0 h-full"
    >
      <Card
        className="
          relative
          h-full
          flex flex-col
          rounded-2xl
          border border-white/10
          bg-white/[0.03]
          backdrop-blur-md
          overflow-hidden
          hover:border-cyan-500/30
          hover:shadow-[0_0_30px_-10px_rgba(6,182,212,0.15)]
          transition-all duration-300
        "
      >
        {/* IMAGE CONTAINER */}
        <div className="relative aspect-[4/3] overflow-hidden bg-gray-900/50">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
            />
          ) : (
             <div className="h-full w-full flex items-center justify-center text-gray-700">No Image</div>
          )}

          {/* Floating Actions on Image */}
          <div className="absolute top-3 right-3 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
             {product.agent_reason && (
                <div className="h-8 w-8 rounded-full bg-black/60 backdrop-blur text-cyan-400 flex items-center justify-center border border-cyan-500/30">
                  <Info className="h-4 w-4" />
                </div>
             )}
          </div>
          
           {/* Quick Buy Overlay on Hover (Desktop) */}
           <div className="absolute inset-x-0 bottom-0 p-4 translate-y-full group-hover:translate-y-0 transition-transform duration-300 bg-gradient-to-t from-black/90 to-transparent hidden md:block">
              <Button
                size="sm"
                className="w-full bg-cyan-500 hover:bg-cyan-400 text-black font-semibold rounded-full"
                disabled={adding || !product.default_variant_id}
                onClick={handleAdd}
              >
                {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : "Quick Add"}
              </Button>
           </div>
        </div>

        {/* CONTENT */}
        <div className="flex flex-col p-4 flex-1 gap-3">
          <div className="space-y-1">
            <h3 className="text-base font-medium text-gray-100 line-clamp-1 group-hover:text-cyan-200 transition-colors">
              {product.name}
            </h3>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white">₹{product.price}</span>
              {product.agent_reason && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-900/40 text-cyan-300 border border-cyan-500/20 md:hidden">
                    AI Pick
                </span>
              )}
            </div>
          </div>

          {/* AI Reason Text (Desktop tooltip style alternative) */}
          {product.agent_reason && (
             <p className="text-xs text-cyan-200/70 line-clamp-2 hidden md:block">
               <span className="text-cyan-400 font-semibold">✨ AI:</span> {product.agent_reason}
             </p>
          )}

          <div className="mt-auto flex gap-2 md:hidden">
            {/* Mobile Actions */}
             <Button
                size="sm"
                variant="secondary"
                className="flex-1 bg-white/10 hover:bg-white/20 text-white border border-white/10"
                disabled={adding || !product.default_variant_id}
                onClick={handleAdd}
             >
                <ShoppingCart className="h-4 w-4" />
             </Button>
             <Button
                size="sm"
                className="flex-[2] bg-cyan-500 hover:bg-cyan-400 text-black"
                onClick={async (e) => {
                  e.stopPropagation();
                  if (!product.default_variant_id) return;
                  trackEvent("buy_now_click", { product_id: product.id, source: railId });
                  await api.post("/orders/checkout", {
                    items: [{ product_variant_id: product.default_variant_id, quantity: 1 }],
                    order_type: "delivery"
                  });
                }}
             >
                Buy Now
             </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}