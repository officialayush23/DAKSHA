import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import api from "@/lib/apiClient";
import { trackProductView, flush } from "@/lib/analytics";

import PDPSkeleton from "@/components/product/PDPSkeleton";
import VariantCarousel from "@/components/product/VariantCarousel";
import VariantSelector from "@/components/product/VariantSelector";
import ProductMeta from "@/components/product/ProductMeta";
import PDPActions from "@/components/product/PDPActions";
import ReviewSection from "@/components/product/ReviewSection";

export default function ProductDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [activeVariant, setActiveVariant] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/products/${id}`)
      .then(res => {
        setData(res.data);
        setActiveVariant(res.data.variants[0] || null);

        trackProductView({
          id: res.data.product.id,
          price: res.data.product.base_price,
        });
      })
      .finally(() => {
        flush();
        setLoading(false);
      });
  }, [id]);

  if (loading) return <PDPSkeleton />;
  if (!data) return null;

  const { product, variants, reviews } = data;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 grid md:grid-cols-2 gap-10">
      
      {/* LEFT */}
      <div className="space-y-4">
        <VariantCarousel
          variants={variants}
          activeVariant={activeVariant}
          onChange={setActiveVariant}
        />
      </div>

      {/* RIGHT */}
      <div className="space-y-6">
        <ProductMeta
          product={product}
          price={activeVariant?.price}
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

      {/* REVIEWS */}
      <div className="md:col-span-2">
        <ReviewSection
          productId={product.id}
          reviews={reviews}
        />
      </div>
    </div>
  );
}
