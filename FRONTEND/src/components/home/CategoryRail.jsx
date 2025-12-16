// src/components/home/CategoryRail.jsx

import ProductCardCompact from "./ProductCardCompact";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { trackEvent } from "@/lib/analytics";

export default function CategoryRail({ title, gender, items }) {
  const navigate = useNavigate();

  return (
    <section className="px-4 md:px-8 mt-10">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">{title}</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            trackEvent("cta_click", { type: "see_more", gender });
            navigate(`/products?gender=${gender}`);
          }}
        >
          See more →
        </Button>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-2">
        {items.slice(0, 8).map(p => (
          <ProductCardCompact key={p.id} product={p} />
        ))}
      </div>
    </section>
  );
}
