// src/modules/store_manager/pages/InventoryList.jsx

import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom"; // 1. Use Context
import api from "@/lib/apiClient"; 
import { 
  Search, MapPin, Package, Filter, Loader2, Box, AlertCircle, RefreshCw 
} from "lucide-react";

import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function InventoryList() {
  const { store_id } = useOutletContext(); // Get Active Store ID
  
  const [loading, setLoading] = useState(true);
  const [inventory, setInventory] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all"); 

  // --- 1. FETCH DATA ---
  const fetchInventory = async () => {
    if (!store_id) return;

    setLoading(true);
    try {
      // Call our new backend endpoint
      const res = await api.get(`/admin/inventory/items/${store_id}`);
      setInventory(res.data || []);
    } catch (err) {
      console.error("Inventory Fetch Error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [store_id]);

  // --- 2. CLIENT-SIDE FILTERING ---
  const filteredInventory = inventory.filter(item => {
    const variant = item.variant || {};
    const product = item.product || {};
    
    // Search Filter (Product Name or SKU)
    const matchesSearch = 
      (product.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (variant.sku || "").toLowerCase().includes(searchQuery.toLowerCase());

    // Status Filter
    let matchesStatus = true;
    if (filterStatus === 'low_stock') matchesStatus = item.quantity_on_hand > 0 && item.quantity_on_hand <= 10;
    if (filterStatus === 'out_of_stock') matchesStatus = item.quantity_on_hand === 0;

    return matchesSearch && matchesStatus;
  });

  if (!store_id) return <div className="p-8 text-center text-zinc-500">Please select a store to view inventory.</div>;

  return (
    <div className="space-y-6 animate-in fade-in">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <Package className="h-8 w-8 text-emerald-500" />
            Live Inventory
          </h2>
          <p className="text-zinc-400 text-sm mt-1">
            Real-time stock levels for this location.
          </p>
        </div>
        <div className="flex gap-2">
           <Button variant="outline" size="sm" onClick={fetchInventory} disabled={loading} className="bg-zinc-900 border-zinc-800 text-zinc-300 hover:text-white hover:bg-zinc-800">
             <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
             Refresh
           </Button>
           <Badge variant="outline" className="h-9 px-4 border-zinc-800 bg-zinc-900/50 text-zinc-300 font-medium">
             Total SKUs: <span className="text-white ml-2 font-bold">{filteredInventory.length}</span>
           </Badge>
        </div>
      </div>

      {/* FILTERS TOOLBAR */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-zinc-400" />
          <Input 
            placeholder="Search by Product Name or SKU..." 
            className="pl-10 bg-zinc-900/50 border-zinc-800 text-white h-11 focus:border-emerald-500 placeholder:text-zinc-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-[200px] bg-zinc-900/50 border-zinc-800 text-white h-11">
            <Filter className="mr-2 h-4 w-4 text-zinc-400" />
            <SelectValue placeholder="Filter Status" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
            <SelectItem value="all">All Items</SelectItem>
            <SelectItem value="low_stock" className="text-amber-500">Low Stock (≤ 10)</SelectItem>
            <SelectItem value="out_of_stock" className="text-red-500">Out of Stock (0)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* DATA TABLE */}
      <Card className="bg-zinc-950 border-zinc-800 shadow-xl overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-zinc-900/50 border-b border-zinc-800">
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400 h-12 w-[40%] pl-6">Product</TableHead>
                <TableHead className="text-zinc-400 h-12">Variant</TableHead>
                <TableHead className="text-zinc-400 h-12 text-center">Location</TableHead>
                <TableHead className="text-zinc-400 h-12 text-right pr-6">Stock</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                 <TableRow>
                   <TableCell colSpan={4} className="h-40 text-center">
                     <div className="flex items-center justify-center gap-2 text-zinc-500">
                       <Loader2 className="h-5 w-5 animate-spin" /> Loading Inventory...
                     </div>
                   </TableCell>
                 </TableRow>
              ) : filteredInventory.length === 0 ? (
                 <TableRow>
                   <TableCell colSpan={4} className="h-40 text-center text-zinc-500">
                      <div className="flex flex-col items-center gap-2">
                        <AlertCircle className="h-6 w-6 opacity-50" />
                        No items found matching your filters.
                      </div>
                   </TableCell>
                 </TableRow>
              ) : (
                filteredInventory.map((item) => {
                  const isLow = item.quantity_on_hand <= 10 && item.quantity_on_hand > 0;
                  const isOut = item.quantity_on_hand === 0;

                  return (
                    <TableRow key={item.id} className="border-zinc-900 hover:bg-zinc-900/40 transition-colors">
                      {/* PRODUCT COL */}
                      <TableCell className="py-4 pl-6">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center overflow-hidden">
                            {item.variant?.image_url ? (
                              <img src={item.variant.image_url} alt="img" className="h-full w-full object-cover" />
                            ) : <Box className="h-4 w-4 text-zinc-600" />}
                          </div>
                          <div>
                            <p className="font-medium text-zinc-200 truncate max-w-[200px]">{item.product?.name}</p>
                            <p className="text-xs text-zinc-500 font-mono">SKU: {item.variant?.sku}</p>
                          </div>
                        </div>
                      </TableCell>

                      {/* VARIANT COL */}
                      <TableCell>
                         <div className="flex flex-wrap gap-2">
                            {item.variant?.color_name && (
                                <Badge variant="secondary" className="bg-zinc-900 text-zinc-400 border-zinc-800 text-[10px]">
                                    {item.variant.color_name}
                                </Badge>
                            )}
                            {item.variant?.size_label && (
                                <Badge variant="secondary" className="bg-zinc-900 text-zinc-400 border-zinc-800 text-[10px]">
                                    {item.variant.size_label}
                                </Badge>
                            )}
                         </div>
                      </TableCell>

                      {/* LOCATION COL */}
                      <TableCell className="text-center">
                        <div className="inline-flex items-center gap-2 bg-zinc-900 px-2 py-1 rounded text-xs text-zinc-400 border border-zinc-800">
                           <MapPin className="h-3 w-3 text-zinc-600" />
                           <span className="text-zinc-500">Aisle</span> <span className="text-zinc-300 font-mono">{item.aisle_number || '-'}</span>
                           <span className="text-zinc-700">|</span>
                           <span className="text-zinc-500">Shelf</span> <span className="text-zinc-300 font-mono">{item.shelf_height || '-'}</span>
                        </div>
                      </TableCell>

                      {/* STOCK COL */}
                      <TableCell className="text-right pr-6">
                        <div className="flex flex-col items-end">
                           <span className={`text-lg font-bold font-mono ${isOut ? 'text-red-500' : isLow ? 'text-amber-500' : 'text-emerald-500'}`}>
                             {item.quantity_on_hand}
                           </span>
                           {isOut && <span className="text-[10px] text-red-500 uppercase font-bold">Out of Stock</span>}
                           {isLow && <span className="text-[10px] text-amber-500 uppercase font-bold">Low Stock</span>}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}