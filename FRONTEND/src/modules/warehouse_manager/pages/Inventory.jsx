import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  PackageSearch, Search, AlertTriangle, ArrowUpRight, ArrowDownRight, Loader2, Save
} from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

export default function WarehouseInventory() {
  const { warehouseId } = useOutletContext();
  const [loading, setLoading] = useState(true);
  const [inventory, setInventory] = useState([]);
  const [search, setSearch] = useState("");

  const fetchInventory = async () => {
    if (!warehouseId) return;
    setLoading(true);
    try {
      // Calls GET /admin/warehouse/inventory/{id}
      const res = await api.get(`/admin/warehouse/inventory/${warehouseId}`);
      // Fallback to empty array if mock endpoint returns null
      setInventory(res.data || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load inventory data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [warehouseId]);

  // Mock filtering (replace with API search if dataset is large)
  const filteredItems = inventory.filter(item => 
    item.product_name?.toLowerCase().includes(search.toLowerCase()) ||
    item.sku?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-in fade-in">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-zinc-900 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <PackageSearch className="h-6 w-6 text-red-500" /> Stock Control
          </h2>
          <p className="text-zinc-400 text-sm">Real-time inventory levels for this facility.</p>
        </div>
        
        <div className="relative w-full md:w-80">
           <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
           <Input 
             placeholder="Search SKU or Product Name..." 
             className="pl-9 bg-zinc-900 border-zinc-800 text-white focus-visible:ring-red-500"
             value={search}
             onChange={(e) => setSearch(e.target.value)}
           />
        </div>
      </div>

      {/* Inventory Table */}
      <Card className="bg-zinc-950 border-zinc-800 overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-zinc-900/50">
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-500">SKU / Variant</TableHead>
                <TableHead className="text-zinc-500">Product Name</TableHead>
                <TableHead className="text-zinc-500 text-right">Available Qty</TableHead>
                <TableHead className="text-zinc-500 text-center">Status</TableHead>
                <TableHead className="text-zinc-500 text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                   <TableCell colSpan={5} className="h-32 text-center"><Loader2 className="animate-spin h-6 w-6 text-red-500 mx-auto"/></TableCell>
                </TableRow>
              ) : filteredItems.length === 0 ? (
                <TableRow>
                   <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                      {inventory.length === 0 ? "No inventory records found. (Backend Mock Empty?)" : "No matching items."}
                   </TableCell>
                </TableRow>
              ) : (
                filteredItems.map((item) => (
                  <TableRow key={item.variant_id} className="border-zinc-800 hover:bg-zinc-900/40">
                    <TableCell className="font-mono text-xs text-zinc-400">{item.sku || "N/A"}</TableCell>
                    <TableCell className="text-zinc-300 font-medium">{item.product_name}</TableCell>
                    <TableCell className="text-right font-mono text-white">{item.quantity}</TableCell>
                    <TableCell className="text-center">
                       {item.quantity < 10 ? (
                         <Badge variant="destructive" className="bg-red-900/20 text-red-400 border-red-900/50">Low Stock</Badge>
                       ) : (
                         <Badge variant="outline" className="border-zinc-700 text-zinc-500">Healthy</Badge>
                       )}
                    </TableCell>
                    <TableCell className="text-right">
                       <AdjustStockDialog item={item} warehouseId={warehouseId} onSuccess={fetchInventory} />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// Sub-component for Adjustment Modal
function AdjustStockDialog({ item, warehouseId, onSuccess }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [adjustment, setAdjustment] = useState(0);
  const [reason, setReason] = useState("");

  const handleAdjust = async () => {
    setLoading(true);
    try {
      await api.post("/admin/warehouse/inventory/adjust", {
        warehouse_id: warehouseId,
        variant_id: item.variant_id,
        quantity_change: parseInt(adjustment),
        reason: reason
      });
      toast.success("Stock updated successfully");
      setOpen(false);
      onSuccess(); // Refresh parent table
    } catch (error) {
      toast.error("Adjustment failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="h-8 text-zinc-400 hover:text-white hover:bg-zinc-800">
           Adjust
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-zinc-950 border-zinc-800 text-white sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Adjust Stock Level</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right text-zinc-400">Product</Label>
            <span className="col-span-3 text-sm font-medium truncate">{item.product_name}</span>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="qty" className="text-right text-zinc-400">Change (+/-)</Label>
            <Input 
              id="qty" 
              type="number" 
              className="col-span-3 bg-black border-zinc-800" 
              placeholder="-5 or 10"
              value={adjustment}
              onChange={(e) => setAdjustment(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="reason" className="text-right text-zinc-400">Reason</Label>
            <Input 
              id="reason" 
              className="col-span-3 bg-black border-zinc-800" 
              placeholder="Damaged / Restock / Audit"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleAdjust} disabled={loading || adjustment == 0} className="bg-red-600 hover:bg-red-700 text-white">
            {loading ? <Loader2 className="animate-spin h-4 w-4"/> : <Save className="h-4 w-4 mr-2"/>}
            Confirm Adjustment
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}