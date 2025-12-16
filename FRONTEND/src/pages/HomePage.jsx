import React, { useEffect, useState } from "react";
import api from "@/lib/apiClient";
import { trackEvent, flush } from "@/lib/analytics";

import HeroSection from "@/components/home/HeroSection";
import OfferStrip from "@/components/home/OfferStrip";
import CategoryRail from "@/components/home/CategoryRail";
import HomeFooter from "@/components/home/HomeFooter";
import BottomNav from "@/components/home/BottomNav";
import HomeSkeleton from "@/components/home/skeletons/HomeSkeleton";

export default function HomePage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    trackEvent("page_enter", { page: "home" });

    let mounted = true;
    api.get("/home")
      .then(res => mounted && setItems(res.data || []))
      .catch(() => mounted && setError(true))
      .finally(() => mounted && setLoading(false));

    return () => {
      trackEvent("page_exit", { page: "home" });
      flush();
      mounted = false;
    };
  }, []);

  if (loading) return <HomeSkeleton />;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Unable to load home.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground pb-20 md:pb-0">
      <HeroSection />

      <OfferStrip />

      <CategoryRail
        title="Trending Now"
        gender="all"
        items={items}
      />

      <HomeFooter />
      <BottomNav />
    </div>
  );
}
