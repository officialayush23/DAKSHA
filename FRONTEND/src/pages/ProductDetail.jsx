import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient";
import {
  trackEvent,
  trackProductView,
  flush
} from "@/lib/analytics";

import VariantCarousel from "@/components/product/VariantCarousel";
import VariantSelector from "@/components/product/VariantSelector";
import ProductMeta from "@/components/product/ProductMeta";
import PDPActions from "@/components/product/PDPActions";
import PDPSkeleton from "@/components/product/PDPSkeleton";

export default function ProductDetailPage() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [variants, setVariants] = useState([]);
  const [activeVariant, setActiveVariant] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    trackEvent("page_enter", { page: "product_detail", product_id: id });

    let mounted = true;

    async function load() {
      const { data, error } = await supabase
        .from("products")
        .select(`
          id, name, description, base_price, gender, style_tags,
          variants:product_variants(
            id, image_url, price_override, color_name, size_label
          )
        `)
        .eq("id", id)
        .single();

      if (!error && mounted) {
        setProduct(data);
        setVariants(data.variants || []);
        setActiveVariant(data.variants?.[0] || null);
        trackProductView(data);
      }

      setLoading(false);
    }

    load();

    return () => {
      flush();
      mounted = false;
    };
  }, [id]);

  if (loading) return <PDPSkeleton />;
  if (!product) return null;

  const effectivePrice =
    activeVariant?.price_override ?? product.base_price;

  return (
    <div className="min-h-screen bg-background text-foreground px-4 pb-24 md:pb-8">
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-10 pt-6">

        {/* LEFT — MEDIA */}
        <VariantCarousel
          variants={variants}
          activeVariant={activeVariant}
          onChange={setActiveVariant}
        />

        {/* RIGHT — DETAILS */}
        <div className="space-y-6">
          <ProductMeta
            product={product}
            price={effectivePrice}
          />

          <VariantSelector
            variants={variants}
            activeVariant={activeVariant}
            onChange={setActiveVariant}
          />

          <PDPActions
            product={product}
            variant={activeVariant}
          />
        </div>
      </div>
    </div>
  );
}
