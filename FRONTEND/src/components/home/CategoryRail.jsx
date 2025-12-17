// src/components/home/CategoryRail.jsx
import ProductCardCompact from "./ProductCardCompact";
import { trackEvent } from "@/lib/analytics";
import { useEffect } from "react";
import { ArrowRight } from "lucide-react";

export default function CategoryRail({ section }) {
  useEffect(() => {
    trackEvent("section_view", {
      section_id: section.id,
      title: section.title,
    });
  }, [section]);

  if (!section.items?.length) return null;

  return (
    <section className="mt-16 max-w-7xl mx-auto px-4 md:px-8">
      <div className="flex items-end justify-between mb-6 px-1">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white mb-1">
            {section.title}
          </h2>
          {section.subtitle && (
            <p className="text-sm text-gray-400 font-light">
              {section.subtitle}
            </p>
          )}
        </div>
        <button className="hidden md:flex items-center gap-1 text-sm text-cyan-400 hover:text-cyan-300 transition-colors cursor-pointer">
            View All <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      <div
        className="
          flex md:grid
          md:grid-cols-4
          gap-5
          overflow-x-auto md:overflow-visible
          pb-8 md:pb-0
          snap-x snap-mandatory md:snap-none
          -mx-4 px-4 md:mx-0 md:px-0
          scrollbar-hide
        "
      >
        {section.items.map((p) => (
          <div key={p.id} className="snap-start h-full">
            <ProductCardCompact
                product={p}
                railId={section.id}
            />
          </div>
        ))}
      </div>
    </section>
  );
}