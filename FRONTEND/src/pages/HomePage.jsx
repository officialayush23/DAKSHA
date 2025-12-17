// src/pages/HomePage.jsx
import React, { useEffect, useState } from "react";
import api from "@/lib/apiClient";
import { trackEvent, flush } from "@/lib/analytics";

import HeroSection from "@/components/home/HeroSection";
import CategoryRail from "@/components/home/CategoryRail";
import HomeFooter from "@/components/home/HomeFooter";
import BottomNav from "@/components/home/BottomNav";
import HomeSkeleton from "@/components/skeletons/HomeSkeleton";
import HomeHeader from "@/components/home/HomeHeader";

export default function HomePage() {
  const [home, setHome] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    trackEvent("page_enter", { page: "home" });

    let mounted = true;
    api.get("/home")
      .then(res => mounted && setHome(res.data))
      .catch(() => mounted && setError(true))
      .finally(() => mounted && setLoading(false));

    return () => {
      trackEvent("page_exit", { page: "home" });
      flush();
      mounted = false;
    };
  }, []);

  if (loading) return <HomeSkeleton />;

  if (error || !home) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
             <p className="text-muted-foreground">Unable to load fashion feed.</p>
             <button onClick={() => window.location.reload()} className="text-cyan-400 hover:underline">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground pb-20 md:pb-0 relative">
      <HomeHeader />
      
      <main className="relative z-10">
          <HeroSection hero={home.hero} />

          {home.sections.map(section => (
            <CategoryRail key={section.id} section={section} />
          ))}
      </main>

      <HomeFooter />
      <BottomNav />
    </div>
  );
}