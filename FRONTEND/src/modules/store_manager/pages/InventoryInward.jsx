// src/modules/store_manager/pages/InventoryInward.jsx

import React, { useState, useEffect, useMemo } from "react";
import { useOutletContext } from "react-router-dom"; // Optimization: Use Context
import api from "@/lib/apiClient"; 
import { 
  Search, PackagePlus, Loader2, Box, ChevronRight, Store, Layers, AlertTriangle
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function InventoryInward() {
  // 1. OPTIMIZATION: Get Store ID from Layout Context (No API call needed)
  const { store_id, store_name } = useOutletContext();

  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [productList, setProductList] = useState([]); 
  const [allProducts, setAllProducts] = useState([]); // For Dropdown
  
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productVariants, setProductVariants] = useState([]);
  
  // Selection State
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);
  const [stockForm, setStockForm] = useState({ quantity: "", aisle: "", shelf: "" });
  const [submitting, setSubmitting] = useState(false);

  // --- INITIAL LOAD ---
  useEffect(() => {
    // Only fetch default products once on mount
    const fetchDefaults = async () => {
      try {
        const res = await api.get("/admin/inventory/products/search");
        setProductList(res.data || []);
        setAllProducts(res.data || []);
      } catch (err) { console.error(err); }
    };
    fetchDefaults();
  }, []);

  // --- SEARCH ---
  const handleSearch = async (e) => {
    e.preventDefault();
    setIsSearching(true);
    try {
      const res = await api.get("/admin/inventory/products/search", { params: { q: searchQuery } });
      setProductList(res.data || []);
    } catch (err) { toast.error("Search failed"); } 
    finally { setIsSearching(false); }
  };

  // --- SELECT PRODUCT ---
  const handleProductSelect = async (productId) => {
    const product = allProducts.find(p => p.id === productId) || productList.find(p => p.id === productId);
    if (!product) return;

    setSelectedProduct(product);
    setProductVariants([]);
    setSelectedColor(null);
    setSelectedSize(null);
    
    // Fetch Variants (Necessary API call)
    try {
      const res = await api.get(`/admin/inventory/products/${product.id}/variants`);
      setProductVariants(res.data || []);
    } catch (err) { toast.error("Failed to load variants"); }
  };

  // --- COMPUTED HELPERS ---
  const availableColors = useMemo(() => [...new Set(productVariants.map(v => v.color_name).filter(Boolean))], [productVariants]);
  
  const availableSizes = useMemo(() => {
    let filtered = productVariants;
    if (selectedColor) filtered = filtered.filter(v => v.color_name === selectedColor);
    return [...new Set(filtered.map(v => v.size_label).filter(Boolean))];
  }, [productVariants, selectedColor]);

  const activeVariant = useMemo(() => {
    return productVariants.find(v => v.color_name === selectedColor && v.size_label === selectedSize);
  }, [selectedColor, selectedSize, productVariants]);


  // --- SUBMIT ---
  const handleConfirmUpdate = async () => {
    if (!store_id) return toast.error("No Active Store Selected.");
    if (!activeVariant) return toast.error("Select Color & Size.");
    if (!stockForm.quantity || parseInt(stockForm.quantity) <= 0) return toast.error("Invalid Quantity.");

    setSubmitting(true);
    try {
      // Single Optimized API call to handle Update OR Insert
      await api.post(`/admin/inventory/inward/${store_id}`, {
        product_variant_id: activeVariant.id,
        quantity: parseInt(stockForm.quantity),
        aisle: stockForm.aisle ? parseInt(stockForm.aisle) : null,
        shelf: stockForm.shelf ? parseInt(stockForm.shelf) : null
      });

      toast.success("Stock Updated Successfully");
      setStockForm(prev => ({ ...prev, quantity: "" }));
      
    } catch (err) {
      toast.error("Failed to update stock");
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (!store_id) return (
      <div className="h-full flex flex-col items-center justify-center text-zinc-500 pt-20">
          <AlertTriangle className="h-10 w-10 mb-2 opacity-50"/>
          <p>Please select a store from the top menu.</p>
      </div>
  );

  return (
    <div className="space-y-8 animate-in fade-in">
      
      {/* HEADER */}
      <div className="flex items-center justify-between border-b border-zinc-900 pb-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <PackagePlus className="h-8 w-8 text-emerald-500" />
            Inward Stock
          </h2>
          <div className="flex items-center gap-2 mt-2 text-sm text-zinc-400">
             <Store className="h-4 w-4" />
             <span>Location: <span className="text-white font-medium">{store_name}</span></span>
             <Badge variant="outline" className="ml-2 text-[10px] border-emerald-900/30 text-emerald-500">Active</Badge>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* --- LEFT: SEARCH (Catalog View) --- */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="bg-zinc-950 border-zinc-800 shadow-sm">
            <CardContent className="p-4 space-y-4">
              
              <div className="space-y-2">
                <Label className="text-xs font-bold text-zinc-500 uppercase">Select Product</Label>
                <Select onValueChange={handleProductSelect}>
                  <SelectTrigger className="w-full bg-black border-zinc-800 text-white"><SelectValue placeholder="Quick Select..." /></SelectTrigger>
                  <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                    {allProducts.map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>

              <div className="relative text-center"><span className="bg-zinc-950 px-2 text-xs uppercase text-zinc-500 relative z-10">Or Search</span><div className="absolute top-1/2 w-full border-t border-zinc-900"></div></div>

              <form onSubmit={handleSearch} className="flex gap-2">
                <Input placeholder="Type Name..." className="bg-black border-zinc-800 text-white" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}/>
                <Button type="submit" className="bg-zinc-800 hover:bg-zinc-700 text-white">
                  {isSearching ? <Loader2 className="h-4 w-4 animate-spin"/> : <Search className="h-4 w-4"/>}
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="space-y-2 h-[400px] overflow-y-auto pr-2 custom-scrollbar">
            {productList.map((prod) => (
              <div key={prod.id} onClick={() => handleProductSelect(prod.id)}
                className={`flex justify-between p-4 rounded-xl border cursor-pointer transition-all ${selectedProduct?.id === prod.id ? "bg-zinc-900 border-emerald-500/50" : "bg-black border-zinc-800 hover:bg-zinc-900"}`}>
                <h4 className={`text-sm font-medium ${selectedProduct?.id === prod.id ? "text-emerald-400" : "text-white"}`}>{prod.name}</h4>
                <ChevronRight className="h-4 w-4 text-zinc-600" />
              </div>
            ))}
          </div>
        </div>

        {/* --- RIGHT: STOCK FORM --- */}
        <div className="lg:col-span-7">
          {selectedProduct ? (
            <Card className="bg-zinc-950 border-zinc-800 shadow-lg sticky top-6">
              <CardHeader className="border-b border-zinc-900 pb-4">
                <CardTitle className="text-white text-xl">{selectedProduct.name}</CardTitle>
                <CardDescription className="text-zinc-400">Configure Stock Entry</CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-8">
                
                {/* Variant Selectors */}
                <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <Label className="text-xs font-bold text-zinc-500 uppercase">Color</Label>
                    <div className="flex flex-wrap gap-2">
                      {availableColors.map(c => (
                        <button key={c} onClick={() => setSelectedColor(c)} className={`px-3 py-1.5 rounded text-sm border ${selectedColor === c ? "bg-white text-black font-bold" : "bg-zinc-900 text-zinc-400 border-zinc-800"}`}>{c}</button>
                      ))}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label className="text-xs font-bold text-zinc-500 uppercase">Size</Label>
                    <div className="flex flex-wrap gap-2">
                      {availableSizes.map(s => (
                        <button key={s} onClick={() => setSelectedSize(s)} className={`px-3 py-1.5 rounded text-sm border ${selectedSize === s ? "bg-white text-black font-bold" : "bg-zinc-900 text-zinc-400 border-zinc-800"}`}>{s}</button>
                      ))}
                    </div>
                  </div>
                </div>

                <Separator className="bg-zinc-900" />

                {/* Input Fields */}
                {activeVariant ? (
                  <div className="space-y-6 animate-in slide-in-from-bottom-2">
                    <div className="flex items-center gap-4 bg-emerald-950/20 p-4 rounded-xl border border-emerald-900/30">
                       <div className="h-12 w-12 rounded bg-black border border-zinc-800 flex items-center justify-center overflow-hidden">
                          {activeVariant.image_url ? <img src={activeVariant.image_url} className="h-full w-full object-cover"/> : <Box className="h-6 w-6 text-emerald-600"/>}
                       </div>
                       <div><p className="text-sm text-emerald-400 font-semibold">Variant Selected</p><p className="text-xs text-zinc-400 font-mono">SKU: {activeVariant.sku}</p></div>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <Label className="text-zinc-400">Quantity to Add</Label>
                        <Input type="number" autoFocus className="h-12 text-lg bg-black border-zinc-800 font-mono" value={stockForm.quantity} onChange={e => setStockForm({...stockForm, quantity: e.target.value})} />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                          <div className="space-y-2"><Label className="text-zinc-500">Aisle</Label><Input className="h-12 bg-black border-zinc-800" value={stockForm.aisle} onChange={e => setStockForm({...stockForm, aisle: e.target.value})} /></div>
                          <div className="space-y-2"><Label className="text-zinc-500">Shelf</Label><Input className="h-12 bg-black border-zinc-800" value={stockForm.shelf} onChange={e => setStockForm({...stockForm, shelf: e.target.value})} /></div>
                      </div>
                    </div>

                    <Button onClick={handleConfirmUpdate} disabled={submitting || !stockForm.quantity} className="w-full h-14 bg-white text-black hover:bg-zinc-200 font-bold text-base rounded-xl">
                      {submitting ? <Loader2 className="animate-spin mr-2"/> : <PackagePlus className="mr-2 h-5 w-5"/>} Add to Inventory
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-10 text-zinc-500 bg-zinc-900/20 rounded-xl border border-zinc-900">
                    <Layers className="h-8 w-8 mx-auto mb-2 opacity-50" />Select Color & Size.
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
             <div className="h-[400px] flex flex-col items-center justify-center border-2 border-dashed border-zinc-900 rounded-xl text-zinc-600">
              <Layers className="h-12 w-12 mb-4 opacity-20" />Select a product to begin.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}