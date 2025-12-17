// FRONTEND/src/pages/ProductDetail.jsx

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

import { useInventorySocket } from "@/hooks/useInventorySocket"; // Import new hook

export default function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate(); // Added navigate
  const [data, setData] = useState(null);
  const [activeVariant, setActiveVariant] = useState(null);
  const [loading, setLoading] = useState(true);
const activeLocationId = activeVariant?.inventory?.[0]?.fulfillment_location_id;

useInventorySocket(activeLocationId, (update) => {
    // Check if the update is for THIS variant
    if (update.product_variant_id === activeVariant?.id) {
       // Optimistically update the quantity in the UI
       setData(prev => {
          const newVariants = prev.variants.map(v => {
             if (v.id === update.product_variant_id) {
                // Update the inventory list inside the variant
                const newInv = v.inventory.map(invItem => {
                   // If we are tracking multiple stores, check store ID too. 
                   // For now, simple update:
                   return { ...invItem, available_qty: update.quantity_on_hand };
                });
                return { ...v, inventory: newInv };
             }
             return v;
          });
          return { ...prev, variants: newVariants };
       });
       setActiveVariant(prev => {
          if (prev.id === update.product_variant_id) {
             const newInv = prev.inventory.map(invItem => ({ ...invItem, available_qty: update.quantity_on_hand }));
             return { ...prev, inventory: newInv };
          }
          return prev;
       });
    }
  });
  
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
