// FRONTEND/src/modules/warehouse_manager/pages/OutboundOrders.jsx

import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  Search, Package, RefreshCw, AlertCircle, ArrowUpDown, Filter, Save, Loader2, Minus, Plus
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

export default function WarehouseInventory() {
  const { warehouse_id } = useOutletContext();
  
  const [loading, setLoading] = useState(true);
  const [inventory, setInventory] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Adjustment Modal State
  const [isAdjustOpen, setIsAdjustOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [adjustQty, setAdjustQty] = useState(0); // The change amount (e.g. +5 or -2)
  const [adjustReason, setAdjustReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // --- FETCH INVENTORY ---
  const fetchInventory = async () => {
    if (!warehouse_id) return;
    setLoading(true);
    try {
      const res = await api.get(`/admin/warehouse/inventory/${warehouse_id}`);
      setInventory(res.data || []);
    } catch (error) {
      console.error("Inventory Fetch Error:", error);
      toast.error("Failed to load inventory.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [warehouse_id]);

  // --- HANDLE SEARCH ---
  const filteredInventory = inventory.filter(item => 
    item.product_variants?.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.product_variants?.products?.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // --- HANDLE ADJUSTMENT ---
  const openAdjustModal = (item) => {
    setSelectedItem(item);
    setAdjustQty(0);
    setAdjustReason("");
    setIsAdjustOpen(true);
  };

  const submitAdjustment = async () => {
    if (adjustQty === 0) return toast.error("Quantity change cannot be zero.");
    
    setSubmitting(true);
    try {
      await api.post("/admin/warehouse/inventory/adjust", {
        warehouse_id: warehouse_id,
        variant_id: selectedItem.product_variant_id,
        quantity_change: parseInt(adjustQty),
        reason: adjustReason || "Manual Adjustment"
      });

      toast.success("Stock updated successfully");
      setIsAdjustOpen(false);
      fetchInventory(); // Refresh list

    } catch (error) {
      toast.error("Adjustment failed.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!warehouse_id) return null;

  return (
    <div className="w-full space-y-6 animate-in fade-in">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Package className="h-8 w-8 text-orange-500" /> Inventory
          </h2>
          <p className="text-zinc-400 text-sm">Manage stock levels for this facility.</p>
        </div>
        <Button onClick={fetchInventory} variant="outline" className="bg-zinc-900 border-zinc-800 text-zinc-300 hover:text-white">
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {/* TOOLBAR */}
      <div className="flex items-center justify-between gap-4 bg-zinc-950 border border-zinc-800 p-2 rounded-xl">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
          <Input
            placeholder="Search by SKU or Product Name..."
            className="pl-9 bg-black border-zinc-800 text-white h-9 focus-visible:ring-0 focus-visible:border-orange-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button variant="ghost" size="sm" className="text-zinc-400 hover:text-white h-9">
          <Filter className="mr-2 h-4 w-4" /> Filter
        </Button>
      </div>

      {/* TABLE */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-950/50 overflow-hidden">
        <Table>
          <TableHeader className="bg-zinc-900">
            <TableRow className="border-zinc-800 hover:bg-zinc-900">
              <TableHead className="text-zinc-400 font-medium">Product Details</TableHead>
              <TableHead className="text-zinc-400 font-medium">SKU</TableHead>
              <TableHead className="text-zinc-400 font-medium">Bin Location</TableHead>
              <TableHead className="text-zinc-400 font-medium text-center">In Stock</TableHead>
              <TableHead className="text-zinc-400 font-medium text-center">Reserved</TableHead>
              <TableHead className="text-right text-zinc-400 font-medium">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              [1,2,3,4,5].map(i => (
                <TableRow key={i} className="border-zinc-800">
                  <TableCell><Skeleton className="h-5 w-40 bg-zinc-900"/></TableCell>
                  <TableCell><Skeleton className="h-4 w-20 bg-zinc-900"/></TableCell>
                  <TableCell><Skeleton className="h-4 w-16 bg-zinc-900"/></TableCell>
                  <TableCell><Skeleton className="h-4 w-12 bg-zinc-900 mx-auto"/></TableCell>
                  <TableCell><Skeleton className="h-4 w-12 bg-zinc-900 mx-auto"/></TableCell>
                  <TableCell><Skeleton className="h-8 w-20 bg-zinc-900 ml-auto"/></TableCell>
                </TableRow>
              ))
            ) : filteredInventory.length === 0 ? (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={6} className="h-48 text-center text-zinc-500">
                  No items found in this warehouse.
                </TableCell>
              </TableRow>
            ) : (
              filteredInventory.map((item) => (
                <TableRow key={item.id} className="border-zinc-800 hover:bg-zinc-900/40 group">
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium text-white">{item.product_variants?.products?.name || "Unknown Product"}</span>
                      <span className="text-xs text-zinc-500">
                        {item.product_variants?.color_name} • {item.product_variants?.size_label}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-xs text-zinc-300 bg-zinc-900 px-2 py-1 rounded">
                      {item.product_variants?.sku}
                    </span>
                  </TableCell>
                  <TableCell>
                    {item.aisle_number ? (
                      <Badge variant="outline" className="border-zinc-700 text-zinc-400">
                        {item.display_location || `A${item.aisle_number}-B${item.bay_number}`}
                      </Badge>
                    ) : <span className="text-zinc-600 text-xs">Unassigned</span>}
                  </TableCell>
                  <TableCell className="text-center">
                    <span className={`font-bold ${item.quantity_on_hand <= (item.low_stock_threshold || 5) ? "text-amber-500" : "text-emerald-500"}`}>
                      {item.quantity_on_hand}
                    </span>
                  </TableCell>
                  <TableCell className="text-center text-zinc-500">
                    {item.quantity_reserved}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button 
                      variant="secondary" 
                      size="sm" 
                      onClick={() => openAdjustModal(item)}
                      className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800"
                    >
                      Adjust
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* ADJUSTMENT DIALOG */}
      <Dialog open={isAdjustOpen} onOpenChange={setIsAdjustOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 text-white sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Adjust Stock Level</DialogTitle>
            <DialogDescription className="text-zinc-400">
              Manually update quantity for <span className="text-white font-medium">{selectedItem?.product_variants?.sku}</span>.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            <div className="flex items-center justify-center gap-6">
               <div className="text-center">
                 <p className="text-xs text-zinc-500 mb-1">Current</p>
                 <span className="text-2xl font-bold text-zinc-300">{selectedItem?.quantity_on_hand}</span>
               </div>
               <ArrowUpDown className="text-zinc-600" />
               <div className="text-center">
                 <p className="text-xs text-zinc-500 mb-1">New Total</p>
                 <span className="text-2xl font-bold text-white">
                   {(selectedItem?.quantity_on_hand || 0) + parseInt(adjustQty || 0)}
                 </span>
               </div>
            </div>

            <div className="space-y-3">
              <Label>Adjustment Amount</Label>
              <div className="flex items-center gap-3">
                <Button 
                  variant="outline" 
                  size="icon"
                  className="h-10 w-10 border-zinc-800 bg-zinc-900 hover:bg-zinc-800"
                  onClick={() => setAdjustQty(prev => prev - 1)}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <Input 
                  type="number" 
                  className="bg-black border-zinc-800 text-center font-mono text-lg h-10"
                  value={adjustQty}
                  onChange={(e) => setAdjustQty(e.target.value)}
                />
                <Button 
                  variant="outline" 
                  size="icon"
                  className="h-10 w-10 border-zinc-800 bg-zinc-900 hover:bg-zinc-800"
                  onClick={() => setAdjustQty(prev => parseInt(prev || 0) + 1)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-zinc-500">Use negative numbers to remove stock.</p>
            </div>

            <div className="space-y-2">
              <Label>Reason Code</Label>
              <Input 
                placeholder="e.g. Stock Take, Damaged, Found" 
                className="bg-black border-zinc-800"
                value={adjustReason}
                onChange={(e) => setAdjustReason(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setIsAdjustOpen(false)} className="text-zinc-400 hover:text-white">Cancel</Button>
            <Button onClick={submitAdjustment} disabled={submitting || adjustQty == 0} className="bg-orange-600 hover:bg-orange-700 text-white">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Confirm Update"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}