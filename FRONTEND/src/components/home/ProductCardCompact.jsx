// src/components/home/ProductCardCompact.jsx

import { Card, CardContent } from "@/components/ui/card";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { trackProductClick, trackProductView } from "@/lib/analytics";
import { useEffect, useRef } from "react";

export default function ProductCardCompact({ product }) {
  const navigate = useNavigate();
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let viewed = false;
    const io = new IntersectionObserver(([e]) => {
      if (!viewed && e.isIntersecting) {
        viewed = true;
        trackProductView(product);
      }
    }, { threshold: 0.6 });

    io.observe(el);
    return () => io.disconnect();
  }, [product]);

  return (
    <motion.div
      ref={ref}
      whileHover={{ y: -4 }}
      className="min-w-[160px] md:min-w-[200px]"
      onClick={() => {
        trackProductClick(product);
        navigate(`/products/${product.id}`);
      }}
    >
      <Card className="border border-white/5 bg-card/80 overflow-hidden cursor-pointer">
        <div className="aspect-[3/4] bg-muted">
          {product.image_url && (
            <img
              src={product.image_url}
              className="h-full w-full object-cover"
              alt={product.name}
            />
          )}
        </div>

        <CardContent className="p-3 space-y-1">
          <div className="text-sm font-medium line-clamp-1">
            {product.name}
          </div>
          <div className="text-sm font-semibold">
            ₹{product.base_price}
          </div>

          {product.agent_reason && (
            <p className="text-[11px] text-muted-foreground line-clamp-2">
              {product.agent_reason}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
