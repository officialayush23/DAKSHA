import React, { useEffect, useState } from 'react';
import Layout from '@/components/layout/Layout';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, SlidersHorizontal } from 'lucide-react';
import ProductCard from '@/components/ProductCard';
import ProductFilters from '@/components/ProductFilters';
import { catalogService } from '@/services/api';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const Catalog = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState({ categories: [] });

  const fetchProducts = async (query = "") => {
    setLoading(true);
    try {
      // Calls your backend /catalog/search
      const results = await catalogService.searchProducts(query);
      setProducts(results);
    } catch (error) {
      console.error("Failed to load catalog", error);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchProducts(searchQuery);
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        
        {/* Header & Search */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Catalog</h1>
            <p className="text-muted-foreground mt-1">
              Explore our latest collection driven by AI search.
            </p>
          </div>

          <form onSubmit={handleSearch} className="flex w-full md:w-[400px] gap-2">
            <Input 
              placeholder="Search products (e.g., 'summer dress')..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <Button type="submit" size="icon">
              <Search className="h-4 w-4" />
            </Button>
          </form>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Filters - Sidebar on Desktop */}
          <div className="hidden md:block">
             <ProductFilters activeFilters={filters} onFilterChange={setFilters} />
          </div>

          {/* Filters - Sheet/Drawer on Mobile */}
          <div className="md:hidden w-full">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" className="w-full gap-2">
                  <SlidersHorizontal className="h-4 w-4" /> Filters
                </Button>
              </SheetTrigger>
              <SheetContent side="left">
                <SheetHeader>
                  <SheetTitle>Filters</SheetTitle>
                </SheetHeader>
                <div className="mt-4">
                  <ProductFilters activeFilters={filters} onFilterChange={setFilters} />
                </div>
              </SheetContent>
            </Sheet>
          </div>

          {/* Product Grid */}
          <div className="md:col-span-3">
            {loading ? (
              <div className="flex justify-center py-20">Loading products...</div>
            ) : products.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product) => (
                  <ProductCard key={product.id || product.name} product={product} />
                ))}
              </div>
            ) : (
              <div className="text-center py-20 text-muted-foreground bg-secondary/20 rounded-lg">
                <p>No products found matching your search.</p>
                <Button variant="link" onClick={() => {
                  setSearchQuery("");
                  fetchProducts("");
                }}>
                  Clear Search
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Catalog;