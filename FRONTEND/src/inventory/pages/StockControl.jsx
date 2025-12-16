import React, { useState } from "react";
import { Search, Save, Package, AlertCircle } from "lucide-react";
import { inventoryService } from "@/services/inventoryService"; // Import the service
import { toast } from "sonner"; // For notifications

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";

export default function StockControl() {
  // State Management
  const [sku, setSku] = useState("");
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState(null); // Stores the API result
  const [newQuantity, setNewQuantity] = useState("");

  // TODO: In a real app, get this from your AuthContext
  const CURRENT_STORE_ID = "store-uuid-placeholder"; 

  // 1. Function to Look Up Stock
  const handleCheckStock = async (e) => {
    e.preventDefault();
    if (!sku) return;

    setLoading(true);
    setStockData(null);

    try {
      // Call the Service
      const response = await inventoryService.checkStock(sku, CURRENT_STORE_ID);
      
      // Assuming API returns: { name, quantity_on_hand, quantity_reserved, variant_id, ... }
      // Mocking data for display if API isn't connected yet:
      const data = response.data || { 
        name: "Mock Product Name", 
        quantity_on_hand: 42, 
        quantity_reserved: 5,
        sku: sku
      };
      
      setStockData(data);
      setNewQuantity(data.quantity_on_hand); // Pre-fill update input
    } catch (error) {
      console.error(error);
      toast.error("Product not found or system error.");
    } finally {
      setLoading(false);
    }
  };

  // 2. Function to Update Stock
  const handleUpdateStock = async () => {
    if (!stockData) return;

    try {
      await inventoryService.updateStock({
        variant_id: stockData.variant_id, // Ensure your API check returns this
        store_id: CURRENT_STORE_ID,
        quantity_on_hand: parseInt(newQuantity)
      });
      
      toast.success("Inventory updated successfully!");
      
      // Update local state to reflect change
      setStockData({ ...stockData, quantity_on_hand: parseInt(newQuantity) });
      
    } catch (error) {
      console.error(error);
      toast.error("Failed to update inventory.");
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h3 className="text-lg font-medium">Inventory Management</h3>
        <p className="text-sm text-muted-foreground">
          Look up products by SKU and adjust stock levels.
        </p>
      </div>
      <Separator />

      {/* --- SEARCH SECTION --- */}
      <Card>
        <CardHeader>
          <CardTitle>Product Lookup</CardTitle>
          <CardDescription>Enter the SKU or scan the barcode.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCheckStock} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="SKU-12345..." 
                className="pl-9"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? "Checking..." : "Search"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* --- RESULTS & ACTION SECTION --- */}
      {stockData && (
        <Card className="animate-in fade-in-50 duration-500">
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl">{stockData.name}</CardTitle>
                <CardDescription className="mt-1">SKU: {stockData.sku}</CardDescription>
              </div>
              <Badge variant="outline" className="flex items-center gap-1">
                <Package className="h-3 w-3" />
                In Stock
              </Badge>
            </div>
          </CardHeader>
          
          <CardContent className="grid gap-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4 pt-4">
              <div className="flex flex-col gap-1 p-4 bg-muted/50 rounded-lg">
                <span className="text-xs font-medium text-muted-foreground uppercase">Current On Hand</span>
                <span className="text-2xl font-bold tracking-tight">{stockData.quantity_on_hand}</span>
              </div>
              <div className="flex flex-col gap-1 p-4 bg-muted/50 rounded-lg">
                <span className="text-xs font-medium text-muted-foreground uppercase">Reserved (Orders)</span>
                <span className="text-2xl font-bold tracking-tight text-orange-600">{stockData.quantity_reserved}</span>
              </div>
            </div>

            {/* Update Form */}
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Update Quantity On Hand
              </label>
              <div className="flex gap-2">
                <Input 
                  type="number" 
                  value={newQuantity} 
                  onChange={(e) => setNewQuantity(e.target.value)}
                />
                <Button onClick={handleUpdateStock} className="min-w-[120px]">
                  <Save className="mr-2 h-4 w-4" />
                  Save
                </Button>
              </div>
              <p className="text-[0.8rem] text-muted-foreground flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                This will overwrite the current stock count.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}