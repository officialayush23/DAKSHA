import React, { useEffect, useState } from "react";
import api from "@/lib/apiClient";
import { trackEvent, flush } from "@/lib/analytics";

import HeroSection from "@/components/home/HeroSection";
import OfferStrip from "@/components/home/OfferStrip";
import CategoryRail from "@/components/home/CategoryRail";
import TrendingRail from "@/components/home/TrendingRail";
import AIPicksRail from "@/components/home/AIPicksRail";
import HomeFooter from "@/components/home/HomeFooter";
import BottomNav from "@/components/home/BottomNav";
import HomeSkeleton from "@/components/home/skeletons/HomeSkeleton";

export default function HomePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    trackEvent("page_enter", { page: "home" });

    let mounted = true;
    api.get("/home")
      .then(res => mounted && setData(res.data))
      .catch(() => mounted && setError(true))
      .finally(() => mounted && setLoading(false));

    return () => {
      trackEvent("page_exit", { page: "home" });
      flush();
      mounted = false;
    };
  }, []);

  if (loading) return <HomeSkeleton />;

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Unable to load home.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground pb-20 md:pb-0">
      <HeroSection hero={data.hero} />

      <OfferStrip />

      <CategoryRail
        title="Men"
        gender="men"
        items={data.sections.find(s => s.id === "trending")?.items || []}
      />

      <CategoryRail
        title="Women"
        gender="women"
        items={data.sections.find(s => s.id === "trending")?.items || []}
      />

      <CategoryRail
        title="Kids"
        gender="kids"
        items={data.sections.find(s => s.id === "trending")?.items || []}
      />

      <TrendingRail
        items={data.sections.find(s => s.id === "trending")?.items || []}
      />

      <AIPicksRail
        items={data.sections.find(s => s.id === "personalized")?.items || []}
      />

      <HomeFooter />
      <BottomNav />
    </div>
  );
}
