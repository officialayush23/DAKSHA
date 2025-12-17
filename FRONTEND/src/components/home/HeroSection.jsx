// src/components/home/HeroSection.jsx
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { trackEvent } from "@/lib/analytics";
import { ArrowRight, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

export default function HeroSection({ hero }) {
  const navigate = useNavigate();

  if (!hero) return null;

  return (
    <section className="px-4 md:px-8 mt-8 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden rounded-[2.5rem] border border-white/10 bg-gradient-to-br from-gray-900 to-black p-8 md:p-20 shadow-2xl"
      >
        {/* Background Effects */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyan-500/20 blur-[100px] rounded-full translate-x-1/3 -translate-y-1/3 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-indigo-500/10 blur-[80px] rounded-full -translate-x-1/3 translate-y-1/3 pointer-events-none" />

        {/* Mesh Grid Overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] opacity-20" />

        <div className="relative z-10 max-w-2xl space-y-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium uppercase tracking-wider">
            <Sparkles className="h-3 w-3" />
            New Collection Dropped
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-white leading-[1.1]">
            {hero.title}
          </h1>

          <p className="text-lg text-gray-400 leading-relaxed max-w-lg">
            {hero.subtitle}
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            <Button
              size="lg"
              className="rounded-full h-14 px-8 bg-cyan-400 text-black hover:bg-cyan-300 font-semibold shadow-[0_0_20px_rgba(34,211,238,0.4)] hover:shadow-[0_0_30px_rgba(34,211,238,0.6)] transition-all"
              onClick={() => {
                trackEvent("hero_cta_click", { label: hero.cta.label });
                navigate(hero.cta.href);
              }}
            >
              {hero.cta.label}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            
            <Button
                variant="outline"
                size="lg"
                className="rounded-full h-14 px-8 border-white/20 hover:bg-white/5 text-white"
            >
                View Lookbook
            </Button>
          </div>
        </div>
      </motion.div>
    </section>
  );
}