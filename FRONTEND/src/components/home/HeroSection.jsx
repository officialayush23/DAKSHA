// src/components/home/HeroSection.jsx
import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Bot, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function HeroSection({ hero }) {
  const navigate = useNavigate();

  if (!hero) return null;

  return (
    <section className="relative h-[500px] md:h-[600px] w-full overflow-hidden flex items-center justify-center">
      {/* Background Image */}
      <div className="absolute inset-0 z-0">
        <img
          src={hero.image_url || "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&q=80"}
          alt="Hero"
          className="h-full w-full object-cover brightness-[0.6]"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="relative z-10 text-center space-y-6 px-4 max-w-3xl animate-fade-in-up">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-medium text-cyan-300">
           <Sparkles className="h-3 w-3" />
           <span>New AI Collection</span>
        </div>
        
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white drop-shadow-xl">
          {hero.title}
        </h1>
        
        <p className="text-lg md:text-xl text-gray-200 max-w-xl mx-auto leading-relaxed">
          {hero.subtitle}
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
          <Button 
            size="lg" 
            className="bg-primary text-primary-foreground hover:bg-primary/90 gap-2 h-12 px-8 text-base shadow-lg shadow-cyan-500/20"
            onClick={() => navigate("/products")}
          >
            Shop Now <ArrowRight className="h-4 w-4" />
          </Button>

          {/* 🟢 ASK DAKSHA BUTTON */}
          <Button 
            size="lg" 
            variant="secondary"
            className="bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 gap-2 h-12 px-8 text-base"
            onClick={() => navigate("/chat")}
          >
            <Bot className="h-5 w-5 text-cyan-400" />
            Ask Daksha
          </Button>
        </div>
      </div>
    </section>
  );
}