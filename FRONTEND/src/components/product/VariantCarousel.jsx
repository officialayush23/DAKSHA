// src/components/product/VariantCarousel.jsx

import {
  Carousel,
  CarouselContent,
  CarouselItem
} from "@/components/ui/carousel";

export default function VariantCarousel({
  variants,
  activeVariant,
  onChange
}) {
  return (
    <Carousel className="w-full">
      <CarouselContent>
        {variants.map(v => (
          <CarouselItem key={v.id}>
            <div
              className={`aspect-square rounded-xl overflow-hidden border cursor-pointer
                ${activeVariant?.id === v.id ? "border-white" : "border-white/10"}`}
              onClick={() => onChange(v)}
            >
              {v.image_url && (
                <img
                  src={v.image_url}
                  alt=""
                  className="h-full w-full object-cover"
                />
              )}
            </div>
          </CarouselItem>
        ))}
      </CarouselContent>
    </Carousel>
  );
}
