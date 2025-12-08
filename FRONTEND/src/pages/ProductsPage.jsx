import React, { useEffect, useState } from "react";
import api from "@/lib/apiClient";

import Filters from "@/components/products/Filters";
import SortBar from "@/components/products/SortBar";
import ProductCard from "@/components/products/ProductCard";

import { Skeleton } from "@/components/ui/skeleton";

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // filters
  const [category, setCategory] = useState(null);
  const [brand, setBrand] = useState(null);
  const [sort, setSort] = useState("newest");

  useEffect(() => {
    fetchProducts();
  }, [category, brand, sort]);

  const fetchProducts = async () => {
    setLoading(true);

    try {
      const res = await api.get("/products", {
        params: {
          category,
          brand,
          sort,
        },
      });

      setProducts(res.data);
    } catch (err) {
      console.error("Failed to load products:", err);
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <h1 className="text-3xl font-bold tracking-tight mb-6">Products</h1>

      <div className="grid grid-cols-1 md:grid-cols-[250px_1fr] gap-6">
        {/* Filters */}
        <Filters setCategory={setCategory} setBrand={setBrand} />

        <div className="flex flex-col gap-4">
          <SortBar sort={sort} setSort={setSort} />

          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-64 w-full rounded-xl" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
