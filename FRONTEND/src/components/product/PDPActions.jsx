//  src/components/product/PDPActions.jsx

import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { trackAddToCart, flush } from "@/lib/analytics";
import api from "@/lib/apiClient";

export default function PDPActions({ product, variant }) {
  const [loading, setLoading] = useState(false);

  async function addToCart() {
    if (!variant) return;

    setLoading(true);
    try {
      await api.post("/cart/add", {
        variant_id: variant.id,
        quantity: 1
      });

      trackAddToCart(product, 1, { source: "pdp" });
      flush();
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button
      size="lg"
      className="w-full"
      onClick={addToCart}
      disabled={loading || !variant}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        "Add to Cart"
      )}
    </Button>
  );
}
