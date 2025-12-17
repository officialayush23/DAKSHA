// FRONTEND/src/components/home/OfferStrip.jsx

import { Button } from "@/components/ui/button";
import { trackEvent } from "@/lib/analytics";
import { useNavigate } from "react-router-dom";

export default function OfferRail({ offers }) {
  const nav = useNavigate();
  if (!offers?.length) return null;

  return (
    <section className="px-4 md:px-8 mt-6">
      <div className="flex gap-4 overflow-x-auto">
        {offers.map(o => (
          <div
            key={o.id}
            className="min-w-[260px] rounded-2xl border bg-card p-5"
          >
            <h3 className="font-semibold">{o.label}</h3>
            <p className="text-sm text-muted-foreground mt-1">
              {o.description}
            </p>
            <Button
              size="sm"
              className="mt-3"
              onClick={() => {
                trackEvent("offer_click", { offer_id: o.id });
                nav(o.cta);
              }}
            >
              Shop now
            </Button>
          </div>
        ))}
      </div>
    </section>
  );
}
