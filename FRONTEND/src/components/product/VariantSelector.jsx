// src/components/product/VariantSelector.jsx

import { Button } from "@/components/ui/button";
import { trackEvent } from "@/lib/analytics";

export default function VariantSelector({
  variants,
  activeVariant,
  onChange
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Variants</p>

      <div className="flex flex-wrap gap-2">
        {variants.map(v => (
          <Button
            key={v.id}
            variant={activeVariant?.id === v.id ? "secondary" : "outline"}
            size="sm"
            onClick={() => {
              trackEvent("variant_select", { variant_id: v.id });
              onChange(v);
            }}
          >
            {v.color_name || "Default"}
            {v.size_label && ` · ${v.size_label}`}
          </Button>
        ))}
      </div>
    </div>
  );
}
