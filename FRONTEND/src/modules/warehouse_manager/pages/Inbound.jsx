import React, { useState } from "react";
import { useOutletContext } from "react-router-dom";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  ClipboardList, Search, Plus, CheckCircle, Loader2, PackageOpen, ScanLine
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function Inbound() {
  const { warehouse_id } = useOutletContext();
  
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [cart, setCart] = useState([]); // Items to be inwardly processed
  const [submitting, setSubmitting] = useState(false);

  // --- SEARCH CATALOG TO ADD ---
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery) return;
    
    setLoading(true);
    try {
        // Reuse Catalog Admin Search endpoint to find items to receive
        const res = await api.get("/admin/catalog/products", { params: { q: searchQuery } });
        
        // In a real app, you would fetch variants specifically. 
        // For this UI demo, we assume the search returns products we can select.
        setSearchResults(res.data || []);
    } catch (error) {
        toast.error("Search failed");
    } finally {
        setLoading(false);
    }
  };

  // --- ADD TO INBOUND LIST ---
  const addToInbound = (product) => {
      // Mocking a variant selection for the UI flow
      // Ideally, you'd show a modal to select Size/Color variant here
      const newItem = {
          temp_id: Date.now(),
          product_name: product.name,
          sku: "VAR-" + product.id.slice(0,4).toUpperCase(), // Mock SKU
          product_variant_id: "demo-variant-id", // Needs real ID in prod logic
          quantity: 1
      };
      setCart([...cart, newItem]);
      setSearchResults([]); 
      setSearchQuery("");
  };

  const updateQuantity = (id, delta) => {
      setCart(cart.map(item => 
          item.temp_id === id ? { ...item, quantity: Math.max(1, item.quantity + delta) } : item
      ));
  };

  const removeItem = (id) => {
      setCart(cart.filter(item => item.temp_id !== id));
  };

  // --- SUBMIT INWARD ---
  const handleConfirmInward = async () => {
      if (cart.length === 0) return;
      setSubmitting(true);
      
      try {
          // Loop through cart and submit adjustments
          // In production, use a dedicated bulk endpoint: POST /admin/warehouse/inbound/bulk
          for (const item of cart) {
             await api.post("/admin/warehouse/inventory/adjust", {
                 warehouse_id: warehouse_id,
                 variant_id: item.product_variant_id, // Ensure this is valid in your DB
                 quantity_change: item.quantity,
                 reason: "Inbound Shipment / Stock In"
             });
          }
          
          toast.success("Inbound processed successfully");
          setCart([]);
      } catch (error) {
          console.error(error);
          toast.error("Failed to process inbound.");
      } finally {
          setSubmitting(false);
      }
  };

  if (!warehouse_id) return null;

  return (
    <div className="w-full space-y-6 animate-in fade-in">
      
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          <ClipboardList className="h-8 w-8 text-blue-500" /> Inbound Processing
        </h2>
        <p className="text-zinc-400 text-sm">Receive goods and update warehouse inventory.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* SEARCH PANEL */}
          <Card className="bg-zinc-950 border-zinc-800 text-white lg:col-span-1">
              <CardHeader>
                  <CardTitle className="text-lg font-medium">Add Items</CardTitle>
                  <CardDescription>Search catalog to receive stock.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                  <form onSubmit={handleSearch} className="flex gap-2">
                      <Input 
                        placeholder="Product Name or SKU..." 
                        className="bg-black border-zinc-800" 
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                      />
                      <Button type="submit" variant="secondary" className="bg-zinc-800 text-white" disabled={loading}>
                          {loading ? <Loader2 className="animate-spin h-4 w-4"/> : <Search className="h-4 w-4"/>}
                      </Button>
                  </form>

                  {/* Search Results Area */}
                  {searchResults.length > 0 && (
                      <div className="border border-zinc-800 rounded-md overflow-hidden max-h-60 overflow-y-auto">
                          {searchResults.map(prod => (
                              <div key={prod.id} className="p-3 bg-zinc-900/50 hover:bg-zinc-900 flex justify-between items-center cursor-pointer" onClick={() => addToInbound(prod)}>
                                  <div>
                                      <p className="text-sm font-medium text-white">{prod.name}</p>
                                      <p className="text-xs text-zinc-500">Base: ₹{prod.base_price}</p>
                                  </div>
                                  <Plus className="h-4 w-4 text-zinc-400" />
                              </div>
                          ))}
                      </div>
                  )}
              </CardContent>
          </Card>

          {/* MANIFEST LIST */}
          <Card className="bg-zinc-950 border-zinc-800 text-white lg:col-span-2 min-h-[500px] flex flex-col">
              <CardHeader className="border-b border-zinc-900 pb-4 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-medium flex items-center gap-2">
                        <PackageOpen className="h-5 w-5 text-emerald-500" /> Receiving Manifest
                    </CardTitle>
                    <CardDescription>Items to be added to stock.</CardDescription>
                  </div>
                  <Badge variant="outline" className="border-zinc-700 text-zinc-400">{cart.length} items</Badge>
              </CardHeader>
              
              <CardContent className="p-0 flex-1">
                  <Table>
                      <TableHeader className="bg-zinc-900/50">
                          <TableRow className="border-zinc-800 hover:bg-transparent">
                              <TableHead className="text-zinc-400">Item Details</TableHead>
                              <TableHead className="text-zinc-400 text-center">Qty</TableHead>
                              <TableHead className="text-zinc-400 text-right pr-6">Action</TableHead>
                          </TableRow>
                      </TableHeader>
                      <TableBody>
                          {cart.length === 0 ? (
                              <TableRow className="hover:bg-transparent">
                                  <TableCell colSpan={3} className="h-64 text-center text-zinc-500">
                                      <div className="flex flex-col items-center gap-2">
                                          <ScanLine className="h-10 w-10 opacity-20" />
                                          <p>Scan or search items to begin.</p>
                                      </div>
                                  </TableCell>
                              </TableRow>
                          ) : (
                              cart.map(item => (
                                  <TableRow key={item.temp_id} className="border-zinc-800 hover:bg-zinc-900/30">
                                      <TableCell>
                                          <div className="flex flex-col">
                                              <span className="font-medium">{item.product_name}</span>
                                              <span className="text-xs text-zinc-500 font-mono">{item.sku}</span>
                                          </div>
                                      </TableCell>
                                      <TableCell className="text-center">
                                          <div className="flex items-center justify-center gap-3">
                                              <Button variant="ghost" size="icon" className="h-6 w-6 rounded-full border border-zinc-700" onClick={() => updateQuantity(item.temp_id, -1)}>-</Button>
                                              <span className="w-8 text-center font-mono">{item.quantity}</span>
                                              <Button variant="ghost" size="icon" className="h-6 w-6 rounded-full border border-zinc-700" onClick={() => updateQuantity(item.temp_id, 1)}>+</Button>
                                          </div>
                                      </TableCell>
                                      <TableCell className="text-right pr-6">
                                          <Button variant="ghost" size="sm" className="text-red-500 hover:bg-red-950/20" onClick={() => removeItem(item.temp_id)}>Remove</Button>
                                      </TableCell>
                                  </TableRow>
                              ))
                          )}
                      </TableBody>
                  </Table>
              </CardContent>

              {/* FOOTER ACTIONS */}
              <div className="p-4 border-t border-zinc-900 bg-zinc-900/20 flex justify-end gap-3">
                  <Button variant="ghost" className="text-zinc-400 hover:text-white" onClick={() => setCart([])} disabled={submitting || cart.length === 0}>Clear All</Button>
                  <Button 
                    className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2" 
                    disabled={submitting || cart.length === 0}
                    onClick={handleConfirmInward}
                  >
                      {submitting ? <Loader2 className="animate-spin h-4 w-4"/> : <CheckCircle className="h-4 w-4" />}
                      Confirm Inward
                  </Button>
              </div>
          </Card>
      </div>

    </div>
  );
}