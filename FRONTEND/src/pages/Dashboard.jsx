// src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/apiClient";
import { Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { motion } from "framer-motion";

// ---------------------------------------------
// Motion presets
// ---------------------------------------------
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};

// ---------------------------------------------
// Custom Home Skeleton (brand-grade)
// ---------------------------------------------
function HomeSkeleton() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <main className="max-w-6xl mx-auto px-4 py-10 space-y-16">
        {/* HERO */}
        <Card className="bg-neutral-900/60 border-border/40">
          <CardHeader className="space-y-4">
            <div className="h-6 w-24 bg-muted/40 rounded" />
            <div className="h-10 w-3/4 bg-muted/40 rounded" />
            <div className="h-4 w-1/2 bg-muted/30 rounded" />
            <div className="flex gap-3 pt-2">
              <div className="h-10 w-32 bg-muted/40 rounded" />
              <div className="h-10 w-32 bg-muted/30 rounded" />
            </div>
          </CardHeader>
        </Card>

        {/* SECTIONS */}
        {[1, 2].map((s) => (
          <div key={s} className="space-y-6">
            <div className="space-y-2">
              <div className="h-6 w-48 bg-muted/40 rounded" />
              <div className="h-4 w-64 bg-muted/30 rounded" />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="h-72 rounded-xl bg-muted/30 animate-pulse"
                />
              ))}
            </div>
          </div>
        ))}
      </main>
    </div>
  );
}

// ---------------------------------------------
// Dashboard Page
// ---------------------------------------------
export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const res = await api.get("/home");
        if (mounted) setData(res.data);
      } catch (e) {
        console.error("Home load failed", e);
        if (mounted) setError(true);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => (mounted = false);
  }, []);

  // ---------------------------------------------
  // State handling
  // ---------------------------------------------
  if (loading) return <HomeSkeleton />;

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground">
          Failed to load home. Please refresh.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Floating Sales Agent */}
      <Button
        size="lg"
        className="fixed bottom-6 right-6 z-50 rounded-full shadow-xl"
        onClick={() => navigate("/chat")}
      >
        <Bot className="h-5 w-5 mr-2" />
        Ask Daksha
      </Button>

      <main className="max-w-6xl mx-auto px-4 py-10 space-y-16">
        {/* HERO */}
        <motion.section
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          transition={{ duration: 0.4 }}
        >
          <Card className="bg-gradient-to-br from-neutral-900 to-neutral-950 border-border/40">
            <CardHeader className="space-y-4">
              <Badge variant="outline" className="w-fit">
                AI Curated
              </Badge>

              <CardTitle className="text-4xl">
                {data.hero.title}
              </CardTitle>

              <CardDescription className="text-base max-w-xl">
                {data.hero.subtitle}
              </CardDescription>

              <div className="flex gap-3 pt-2">
                <Button
                  size="lg"
                  onClick={() => navigate(data.hero.cta.href)}
                >
                  {data.hero.cta.label}
                </Button>

                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate("/chat")}
                >
                  <Bot className="h-4 w-4 mr-2" />
                  Ask Agent
                </Button>
              </div>
            </CardHeader>
          </Card>
        </motion.section>

        {/* SECTIONS */}
        {(data.sections || []).map((section, idx) => (
          <motion.section
            key={section.id}
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            transition={{ duration: 0.4, delay: idx * 0.05 }}
            className="space-y-6"
          >
            <div>
              <h2 className="text-2xl font-semibold">
                {section.title}
              </h2>
              <p className="text-sm text-muted-foreground">
                {section.subtitle}
              </p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {section.items.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          </motion.section>
        ))}
      </main>
    </div>
  );
}

// ---------------------------------------------
// Product Card
// ---------------------------------------------
function ProductCard({ product }) {
  const navigate = useNavigate();

  return (
    <motion.div
      whileHover={{ y: -6 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <Card
        onClick={() => navigate(`/products/${product.id}`)}
        className="cursor-pointer overflow-hidden bg-card/80 backdrop-blur border-border/40"
      >
        <div className="aspect-[3/4] bg-muted flex items-center justify-center">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-muted-foreground text-sm">
              No image
            </span>
          )}
        </div>

        <CardContent className="p-4 space-y-2">
          <div className="font-medium line-clamp-1">
            {product.name}
          </div>
          <div className="text-sm text-muted-foreground">
            ₹{product.base_price}
          </div>

          {product.agent_reason && (
            <div className="text-xs text-muted-foreground bg-muted/40 rounded-md p-2">
              {product.agent_reason}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
