import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Search, Plus, MoreHorizontal, Layers, Edit, EyeOff, Eye, Copy, Check, Package, Filter, ArrowUpDown, Loader2
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/apiClient"; // 1. Use API Client

// --- UI COMPONENTS ---
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function ProductList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState(null);

  // --- FETCH PRODUCTS ---
  const fetchProducts = async (query = "") => {
    setLoading(true);
    try {
      // Calls GET /admin/catalog/products?q=...
      const res = await api.get("/admin/catalog/products", {
        params: { q: query }
      });
      setProducts(res.data || []);
    } catch (error) {
      console.error("Failed to fetch products", error);
      toast.error("Failed to load products.");
      setProducts([]); 
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  // --- ACTIONS ---

  const handleSearch = (e) => {
    e.preventDefault();
    fetchProducts(searchQuery);
  };

  const copyToClipboard = (id) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    toast.success("ID Copied!");
    setTimeout(() => setCopiedId(null), 2000);
  };

  // ✅ TOGGLE STATUS (Via API)
  const handleToggleStatus = async (productId) => {
    try {
      // 1. Optimistic UI Update (Update state immediately for speed)
      setProducts(prev => prev.map(p => 
        p.id === productId ? { ...p, is_active: !p.is_active } : p
      ));

      // 2. Call API in background
      await api.patch(`/admin/catalog/products/${productId}/status`);
      
      toast.success("Status Updated");

    } catch (error) {
      console.error("Update failed:", error);
      toast.error("Failed to update status.");
      fetchProducts(searchQuery); // Revert on error
    }
  };

  // Navigate to Create page with ID (Logic for Edit mode needs to be in CreateProduct.jsx)
  const handleEdit = (productId) => {
    navigate(`/catalog/create-product?id=${productId}`);
  };

  return (
    <div className="min-h-screen bg-black text-white font-sans flex justify-center py-10 px-6 animate-in fade-in">
      
      <div className="w-full max-w-7xl space-y-6">
        
        {/* --- HEADER --- */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <div className="p-2 bg-zinc-900 rounded-lg border border-zinc-800">
                <Package className="h-6 w-6 text-white" />
              </div>
              Global Catalog
            </h2>
            <p className="text-zinc-400 text-sm ml-1 max-w-lg">
              Centralized view of all parent product definitions.
            </p>
          </div>
          <Button 
            onClick={() => navigate("/catalog/create-product")} 
            className="bg-white text-black hover:bg-zinc-200 h-10 px-6 font-medium transition-transform active:scale-95"
          >
            <Plus className="mr-2 h-4 w-4" /> Create Product
          </Button>
        </div>

        {/* --- TOOLBAR --- */}
        <div className="flex items-center justify-between gap-4 bg-zinc-950 border border-zinc-800 p-2 rounded-xl">
            <form onSubmit={handleSearch} className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <Input
                placeholder="Search products by name..."
                className="pl-9 bg-black border-zinc-800 text-white placeholder:text-zinc-600 h-9 focus-visible:ring-0 focus-visible:border-zinc-600 rounded-lg"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>
            
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-white h-9">
                <Filter className="mr-2 h-4 w-4" /> Filter
              </Button>
              <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-white h-9">
                <ArrowUpDown className="mr-2 h-4 w-4" /> Sort
              </Button>
            </div>
        </div>

        {/* --- PRODUCT TABLE --- */}
        <Card className="bg-zinc-950 border-zinc-800 shadow-sm overflow-hidden">
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-zinc-900/50">
                <TableRow className="border-zinc-800 hover:bg-transparent">
                  <TableHead className="w-[400px] text-zinc-500 h-11 pl-6 font-medium">Product Details</TableHead>
                  <TableHead className="text-zinc-500 h-11 font-medium">Category</TableHead>
                  <TableHead className="text-zinc-500 h-11 font-medium">Gender</TableHead>
                  <TableHead className="text-zinc-500 h-11 font-medium">Base Price</TableHead>
                  <TableHead className="text-zinc-500 h-11 font-medium">Status</TableHead>
                  <TableHead className="text-right text-zinc-500 h-11 pr-6 font-medium">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  // Skeleton Loading State
                  [1, 2, 3, 4, 5].map((i) => (
                    <TableRow key={i} className="border-zinc-800">
                      <TableCell className="pl-6"><Skeleton className="h-5 w-[200px] bg-zinc-900" /><Skeleton className="h-3 w-[100px] bg-zinc-900 mt-2" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-[100px] bg-zinc-900" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-[80px] bg-zinc-900" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-[80px] bg-zinc-900" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-[60px] bg-zinc-900" /></TableCell>
                      <TableCell className="pr-6"><Skeleton className="h-8 w-8 ml-auto bg-zinc-900" /></TableCell>
                    </TableRow>
                  ))
                ) : products.length === 0 ? (
                  // Empty State
                  <TableRow className="border-zinc-800 hover:bg-transparent">
                    <TableCell colSpan={6} className="h-48 text-center text-zinc-500">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <Package className="h-10 w-10 opacity-20" />
                        <p>No products found matching your search.</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  // Data State
                  products.map((product) => (
                    <TableRow key={product.id} className="border-zinc-800 hover:bg-zinc-900/40 group transition-colors">
                      
                      {/* PRODUCT IDENTITY */}
                      <TableCell className="pl-6 py-4 align-top">
                        <div className="flex flex-col gap-1.5">
                          <span className="text-base text-white font-semibold tracking-tight">{product.name}</span>
                          
                          <div 
                            className="flex items-center gap-1.5 w-fit bg-black border border-zinc-800 rounded px-1.5 py-0.5 cursor-pointer hover:border-zinc-600 transition-colors group/id"
                            onClick={() => copyToClipboard(product.id)}
                            title="Copy UUID"
                          >
                            <span className="text-[10px] font-mono text-zinc-500 group-hover/id:text-zinc-300 transition-colors">
                              {product.id.slice(0, 8)}...
                            </span>
                            {copiedId === product.id ? <Check className="h-2.5 w-2.5 text-emerald-500" /> : <Copy className="h-2.5 w-2.5 text-zinc-600 opacity-0 group-hover/id:opacity-100 transition-opacity" />}
                          </div>
                        </div>
                      </TableCell>
                      
                      <TableCell className="text-zinc-300 py-4 align-top">
                        <Badge variant="outline" className="bg-zinc-950 text-zinc-400 border-zinc-800 font-normal">
                          {product.categories?.name || "Uncategorized"}
                        </Badge>
                      </TableCell>
                      
                      <TableCell className="py-4 align-top">
                        <span className="capitalize text-zinc-400 text-sm">{product.gender}</span>
                      </TableCell>
                      
                      <TableCell className="text-zinc-300 py-4 align-top font-mono text-sm">
                        ₹{product.base_price}
                      </TableCell>
                      
                      <TableCell className="py-4 align-top">
                        {product.is_active ? (
                          <div className="inline-flex items-center px-2 py-1 rounded-full bg-emerald-950/30 border border-emerald-900/50 text-emerald-400 text-xs font-medium">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
                            Active
                          </div>
                        ) : (
                          <div className="inline-flex items-center px-2 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500 text-xs font-medium">
                            <div className="w-1.5 h-1.5 rounded-full bg-zinc-500 mr-1.5" />
                            Draft
                          </div>
                        )}
                      </TableCell>
                      
                      <TableCell className="text-right pr-6 py-4 align-top">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0 text-zinc-500 hover:text-white hover:bg-zinc-800">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-zinc-950 border-zinc-800 text-white min-w-[160px]">
                            <DropdownMenuLabel className="text-xs text-zinc-500 uppercase tracking-wider">Manage</DropdownMenuLabel>
                            
                            <DropdownMenuItem 
                              className="focus:bg-zinc-900 focus:text-white cursor-pointer"
                              onClick={() => navigate(`/catalog/create-variant?product_id=${product.id}`)}
                            >
                              <Layers className="mr-2 h-4 w-4 text-zinc-400" /> Variants
                            </DropdownMenuItem>
                            
                            <DropdownMenuSeparator className="bg-zinc-800" />
                            
                            <DropdownMenuItem 
                              className="focus:bg-zinc-900 focus:text-white cursor-pointer"
                              onClick={() => handleEdit(product.id)}
                            >
                              <Edit className="mr-2 h-4 w-4 text-zinc-400" /> Edit Details
                            </DropdownMenuItem>
                            
                            <DropdownMenuItem 
                              className={`focus:bg-zinc-900 cursor-pointer ${product.is_active ? "text-red-500 focus:text-red-400" : "text-emerald-500 focus:text-emerald-400"}`}
                              onClick={() => handleToggleStatus(product.id)}
                            >
                              {product.is_active ? (
                                <><EyeOff className="mr-2 h-4 w-4" /> Deactivate</>
                              ) : (
                                <><Eye className="mr-2 h-4 w-4" /> Activate</>
                              )}
                            </DropdownMenuItem>
                            
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
        
        <div className="text-center">
            <p className="text-xs text-zinc-600">Showing most recent products first.</p>
        </div>

      </div>
    </div>
  );
}