import React, { useEffect, useState } from "react";
import { ProductService } from "../lib/api";
import { Link } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Search, Loader2, Sparkles, Filter } from "lucide-react";
import { toast } from "sonner";

const CATEGORIES = ["All", "Shoes", "Clothing", "Accessories", "Home"];

export default function ShopPage() {
  const [recommended, setRecommended] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const [searchTerm, setSearchTerm] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");

  useEffect(() => {
    bootstrap();
  }, []);

  const bootstrap = async () => {
    setLoading(true);
    try {
      const [recRes, feedRes] = await Promise.all([
        ProductService.getRecommended?.().catch(() => ({ data: [] })),
        ProductService.getFeed(),
      ]);

      setRecommended(Array.isArray(recRes?.data) ? recRes.data : []);
      setItems(Array.isArray(feedRes?.data) ? feedRes.data : []);
    } catch {
      toast.error("Failed to load shop");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!searchTerm.trim()) {
      bootstrap();
      return;
    }

    try {
      await ProductService.search(searchTerm);
      const res = await ProductService.getFeed(searchTerm);
      setItems(res.data || []);
    } catch {
      toast.error("Search failed");
    }
  };

  const visibleItems =
    activeCategory === "All"
      ? items
      : items.filter(p => p.category === activeCategory);

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <Loader2 className="animate-spin text-zinc-300" />
      </div>
    );
  }

  return (
    <div className="space-y-14">

      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between gap-6">
        <div>
          <h1 className="text-4xl font-serif font-bold">Shop</h1>
          <p className="text-zinc-500 mt-2">
            Ranked by intent, taste, and behavior.
          </p>
        </div>

        <form onSubmit={handleSearch} className="relative w-full md:w-96">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
          <Input
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search linen shirts, sneakers…"
            className="pl-12 py-6 rounded-full"
          />
        </form>
      </div>

      {/* 🔥 RECOMMENDED SECTION */}
      {recommended.length > 0 && (
        <section className="space-y-6">
          <div className="flex items-center gap-2">
            <Sparkles className="text-amber-500" />
            <h2 className="text-2xl font-serif font-bold">
              Recommended for you
            </h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-8">
            {recommended.map(item => (
              <ProductCard key={item.variant_id} item={item} />
            ))}
          </div>
        </section>
      )}

      {/* FILTERS */}
      <div className="flex gap-2 overflow-x-auto">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-5 py-2 rounded-full border text-sm
              ${activeCategory === cat
                ? "bg-black text-white border-black"
                : "bg-white border-zinc-200 text-zinc-600"}
            `}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* MAIN CATALOG */}
      {visibleItems.length === 0 ? (
        <div className="h-64 flex flex-col items-center justify-center text-zinc-400">
          <Filter className="w-10 h-10 mb-3 opacity-30" />
          No products found
        </div>
      ) : (
        <section className="space-y-6">
          <h2 className="text-2xl font-serif font-bold">
            All products
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-8">
            {visibleItems.map(item => (
              <ProductCard key={item.variant_id} item={item} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/* ---------------------------------- */
/* PRODUCT CARD (reused everywhere)   */
/* ---------------------------------- */
function ProductCard({ item }) {
  return (
    <Link
      to={`/dash/product/${item.product_id}`}
      className="group"
    >
      <Card className="border-none bg-transparent">
        <div className="relative aspect-[3/4] bg-zinc-100 rounded-xl overflow-hidden mb-3">
          <img
            src={item.image || "https://placehold.co/600x800"}
            alt={item.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
          />
        </div>

        <CardContent className="p-0">
          <div className="text-xs uppercase text-zinc-400 font-semibold">
            {item.brand}
          </div>
          <div className="font-medium text-lg leading-tight">
            {item.name}
          </div>
        </CardContent>

        <CardFooter className="p-0 mt-1">
          <span className="font-serif text-lg">
            ₹{item.price}
          </span>
        </CardFooter>
      </Card>
    </Link>
  );
}
