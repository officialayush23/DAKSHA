import React, { useState, useEffect, useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import api from "@/lib/apiClient";
import { 
  Search, PackagePlus, Loader2, Box, ChevronRight, Factory, Layers, AlertTriangle
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function Inbound() {
  const { warehouseId } = useOutletContext(); // Get ID from Layout

  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [productList, setProductList] = useState([]); 
  const [allProducts, setAllProducts] = useState([]);
  
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [productVariants, setProductVariants] = useState([]);
  
  // Form State
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);
  const [stockForm, setStockForm] = useState({ quantity: "", aisle: "", shelf: "" });
  const [submitting, setSubmitting] = useState(false);

  // --- INITIAL LOAD ---
  useEffect(() => {
    const fetchDefaults = async () => {
      try {
        // Reuse Catalog Search
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
  const handleConfirmInward = async () => {
    if (!warehouseId) return toast.error("No Active Warehouse.");
    if (!activeVariant) return toast.error("Select Color & Size.");
    const qty = parseInt(stockForm.quantity);
    if (isNaN(qty) || qty <= 0) return toast.error("Invalid Quantity.");

    setSubmitting(true);
    try {
        // Use the Warehouse Inward Endpoint
        // Note: We use the same backend logic as stores, or a specific one if strict separation needed.
        // For simplicity, we reuse the generic inventory adjustment endpoint or the specific inward route if available.
        // Let's use the 'adjust' endpoint which is universal for warehouses.
        
        await api.post("/admin/warehouse/inventory/adjust", {
            variant_id: activeVariant.id,
            quantity_change: qty,
            reason: "Inbound Shipment"
        }, {
            params: { warehouse_id: warehouseId }
        });

      toast.success("Stock Added to Warehouse");
      setStockForm(prev => ({ ...prev, quantity: "" }));
      
    } catch (err) {
      console.error("Inward Error:", err);
      toast.error("Failed to add stock.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!warehouseId) return (
      <div className="h-full flex flex-col items-center justify-center text-zinc-500 pt-20">
          <AlertTriangle className="h-10 w-10 mb-2 opacity-50"/>
          <p>Please select a warehouse.</p>
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
             <Factory className="h-4 w-4" />
             <span>Warehouse: <span className="text-white font-medium">{warehouseId.slice(0,8)}...</span></span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* --- LEFT: SEARCH --- */}
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

        {/* --- RIGHT: FORM --- */}
        <div className="lg:col-span-7">
          {selectedProduct ? (
            <Card className="bg-zinc-950 border-zinc-800 shadow-lg sticky top-6">
              <CardHeader className="border-b border-zinc-900 pb-4">
                <CardTitle className="text-white text-xl">{selectedProduct.name}</CardTitle>
                <CardDescription className="text-zinc-400">Receive Stock</CardDescription>
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

                    <div className="space-y-2">
                        <Label className="text-zinc-400">Quantity to Add</Label>
                        <Input type="number" autoFocus className="h-12 text-lg bg-black border-zinc-800 font-mono" value={stockForm.quantity} onChange={e => setStockForm({...stockForm, quantity: e.target.value})} />
                    </div>

                    <Button onClick={handleConfirmInward} disabled={submitting || !stockForm.quantity} className="w-full h-14 bg-white text-black hover:bg-zinc-200 font-bold text-base rounded-xl">
                      {submitting ? <Loader2 className="animate-spin mr-2"/> : <PackagePlus className="mr-2 h-5 w-5"/>} Add Stock
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