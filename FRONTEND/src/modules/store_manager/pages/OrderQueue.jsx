import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom"; 
import api from "@/lib/apiClient"; // 1. Use API Client
import { 
  Truck, Package, Clock, MoreHorizontal, Printer, MapPin, 
  XCircle, CheckCircle2, Store
} from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";

// --- UI COMPONENTS ---
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";

export default function OrderQueue() {
  const { store_id, store_name } = useOutletContext();

  const [activeTab, setActiveTab] = useState("new");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  // --- FETCH ORDERS (VIA API) ---
  const fetchOrders = async () => {
    if (!store_id) return;

    setLoading(true);
    try {
      // 2. Call the new GET endpoint
      const res = await api.get(`/admin/inventory/orders/${store_id}`, {
        params: { tab: activeTab }
      });
      
      setOrders(res.data || []);

    } catch (error) {
      console.error("Fetch Error:", error);
      toast.error("Failed to load orders.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [activeTab, store_id]);

  // --- UPDATE STATUS (VIA API) ---
  const updateStatus = async (orderId, newStatus) => {
    try {
      // 3. Call the new PATCH endpoint
      await api.patch(`/admin/inventory/orders/${orderId}/status`, {
        status: newStatus
      });
      
      toast.success(`Order marked as ${newStatus.toUpperCase()}`);
      
      // Refresh list to move the order to the correct tab
      fetchOrders();
      setIsDetailsOpen(false);

    } catch (error) {
      console.error("Update Error:", error);
      toast.error("Status update failed.");
    }
  };

  const handlePrintLabel = () => {
    toast.success("Printing Label...");
    setTimeout(() => window.print(), 800);
  };

  if (!store_id) {
    return (
        <div className="h-screen flex items-center justify-center text-zinc-500">
            <div className="text-center">
                <Store className="h-10 w-10 mx-auto mb-2 opacity-50"/>
                <p>Please select a store to view orders.</p>
            </div>
        </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in">
      
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-900 pb-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <Truck className="h-8 w-8 text-emerald-500" />
            Order Queue
          </h2>
          <div className="flex items-center gap-2 mt-2 text-sm text-zinc-400">
             <Store className="h-4 w-4" />
             <span>Location: <span className="text-white font-medium">{store_name}</span></span>
             <Badge variant="outline" className="ml-2 text-[10px] border-emerald-900/30 text-emerald-500">Active</Badge>
          </div>
        </div>
        <div className="flex gap-2">
           <Button variant="outline" onClick={fetchOrders} className="border-zinc-800 text-white hover:bg-zinc-900 h-9">
             Refresh List
           </Button>
        </div>
      </div>

      {/* TABS */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-zinc-900 border border-zinc-800 p-1 h-11 w-full md:w-auto overflow-x-auto justify-start">
          <TabsTrigger value="new" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400 px-6 min-w-[100px]">
             New {activeTab === 'new' && orders.length > 0 && <span className="ml-2 bg-emerald-500/20 text-emerald-400 px-1.5 rounded text-[10px]">{orders.length}</span>}
          </TabsTrigger>
          <TabsTrigger value="processing" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400 px-6 min-w-[100px]">
             Packing
          </TabsTrigger>
          <TabsTrigger value="completed" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white text-zinc-400 px-6 min-w-[100px]">
             Shipped
          </TabsTrigger>
          <TabsTrigger value="cancelled" className="data-[state=active]:bg-red-950/20 data-[state=active]:text-red-400 text-zinc-500 px-6 min-w-[100px]">
             Cancelled
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          
          {loading ? (
             <div className="space-y-4">
               {[1,2,3].map(i => <Skeleton key={i} className="h-32 w-full bg-zinc-900 rounded-xl" />)}
             </div>
          ) : orders.length === 0 ? (
             <div className="flex flex-col items-center justify-center h-48 border-2 border-dashed border-zinc-900 rounded-xl text-zinc-500 bg-zinc-950/30">
               <Package className="h-8 w-8 mb-2 opacity-50" />
               <p>No orders found in {activeTab}.</p>
             </div>
          ) : (
            orders.map((order) => (
              <OrderCard 
                key={order.id} 
                order={order} 
                currentTab={activeTab} 
                onUpdateStatus={updateStatus} 
                onPrintLabel={handlePrintLabel}
                onViewDetails={() => {
                  setSelectedOrder(order);
                  setIsDetailsOpen(true);
                }}
              />
            ))
          )}
          
        </TabsContent>
      </Tabs>

      {/* --- MODAL: ORDER DETAILS --- */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 text-white max-w-2xl">
          {selectedOrder && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center justify-between text-white pr-8">
                  <div className="flex items-center gap-3">
                      <span>Order #{selectedOrder.id.slice(0, 8).toUpperCase()}</span>
                      <Badge className="bg-zinc-800 text-zinc-300 border-zinc-700 capitalize">
                        {selectedOrder.status}
                      </Badge>
                  </div>
                </DialogTitle>
                <DialogDescription className="text-zinc-500">
                  Placed on {format(new Date(selectedOrder.created_at), "MMMM d, yyyy 'at' h:mm a")}
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-6 pt-4">
                
                {/* 1. Customer & Type Grid */}
                <div className="grid grid-cols-2 gap-4 text-sm bg-zinc-900/50 p-4 rounded-lg border border-zinc-900">
                  <div>
                    <p className="text-zinc-500 text-[10px] font-bold uppercase mb-1">Customer User ID</p>
                    <p className="text-white font-medium text-base truncate">{selectedOrder.user_id}</p>
                  </div>
                  <div className="flex flex-col items-end">
                    <p className="text-zinc-500 text-[10px] font-bold uppercase mb-1">Order Type</p>
                    <div className="flex items-center gap-2 text-white capitalize font-medium">
                      {selectedOrder.type === 'pickup' ? (
                        <><MapPin className="h-4 w-4 text-blue-400" /> Pickup</>
                      ) : (
                        <><Truck className="h-4 w-4 text-emerald-400" /> Delivery</>
                      )}
                    </div>
                  </div>
                </div>

                {/* 2. Items List */}
                <div className="space-y-3">
                  <p className="text-zinc-500 text-xs font-bold uppercase tracking-wider">Order Items</p>
                  {selectedOrder.order_items?.map((item) => (
                    <div key={item.id} className="flex justify-between items-start text-sm py-2 border-b border-zinc-900 last:border-0">
                      <div className="flex gap-4">
                        <div className="bg-zinc-900 h-8 w-8 flex items-center justify-center rounded text-zinc-400 font-mono text-xs border border-zinc-800">
                           {item.quantity}x
                        </div>
                        <div>
                          <p className="text-zinc-200 font-medium">{item.product_variants?.products?.name || "Unknown Product"}</p>
                          <p className="text-zinc-500 text-xs">
                             {item.product_variants?.color_name} | {item.product_variants?.size_label} | SKU: {item.product_variants?.sku}
                          </p>
                        </div>
                      </div>
                      <p className="text-zinc-300 font-mono">₹{item.price_at_purchase}</p>
                    </div>
                  ))}
                </div>

                <Separator className="bg-zinc-800" />

                {/* 3. Footer Actions */}
                <div className="flex items-center justify-between">
                   <div className="text-left">
                      <p className="text-xs text-zinc-500">Total Amount</p>
                      <p className="text-2xl font-bold text-white">₹{selectedOrder.total_amount}</p>
                   </div>
                   
                   <div className="flex gap-3">
                      {selectedOrder.status === 'pending' && (
                        <>
                          <Button variant="destructive" size="sm" onClick={() => updateStatus(selectedOrder.id, 'cancelled')}>
                            Cancel
                          </Button>
                          <Button className="bg-white text-black hover:bg-zinc-200" size="sm" onClick={() => updateStatus(selectedOrder.id, 'processing')}>
                            Start Processing
                          </Button>
                        </>
                      )}
                      {selectedOrder.status === 'processing' && (
                        <Button className="bg-emerald-600 hover:bg-emerald-700" size="sm" onClick={() => updateStatus(selectedOrder.id, 'shipped')}>
                          Mark Shipped
                        </Button>
                      )}
                   </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// --- CARD COMPONENT ---
function OrderCard({ order, currentTab, onUpdateStatus, onPrintLabel, onViewDetails }) {
  return (
    <Card className="bg-zinc-950 border-zinc-800 shadow-sm hover:border-zinc-700 transition-colors group">
      <CardHeader className="p-4 flex flex-row items-center justify-between border-b border-zinc-900/50">
        
        {/* Left Info */}
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-center justify-center h-10 w-10 bg-zinc-900 rounded border border-zinc-800">
             <span className="text-[10px] text-zinc-500 uppercase">Order</span>
             <span className="text-xs font-bold text-white">#{order.id.slice(0,4)}</span>
          </div>
          <div className="flex flex-col">
             <span className="text-sm font-medium text-zinc-200">
               Customer: {order.user_id?.slice(0,8)}...
             </span>
             <div className="flex items-center gap-2 text-xs text-zinc-500">
               <Clock className="h-3 w-3" /> 
               {format(new Date(order.created_at), "h:mm a")} 
               <span className="text-zinc-700">|</span>
               {order.type === 'pickup' ? 'Store Pickup' : 'Home Delivery'}
             </div>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          
          {currentTab === 'new' && (
            <Button 
              size="sm" 
              className="bg-white text-black hover:bg-zinc-200 font-medium h-8"
              onClick={() => onUpdateStatus(order.id, 'processing')}
            >
              Start Packing
            </Button>
          )}
          
          {currentTab === 'processing' && (
             <div className="flex gap-2">
                <Button 
                  variant="outline" size="sm" 
                  className="border-zinc-700 text-zinc-300 hover:text-white h-8"
                  onClick={onPrintLabel}
                >
                  <Printer className="mr-2 h-3 w-3" /> Label
                </Button>
                <Button 
                  size="sm" 
                  className="bg-emerald-600 text-white hover:bg-emerald-700 h-8"
                  onClick={() => onUpdateStatus(order.id, 'shipped')}
                >
                  <CheckCircle2 className="mr-2 h-3 w-3" /> Mark Done
                </Button>
             </div>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-500 hover:text-white hover:bg-zinc-800">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-zinc-950 border-zinc-800 text-white min-w-[160px]">
              <DropdownMenuItem onClick={onViewDetails} className="cursor-pointer focus:bg-zinc-900 py-2">
                View Full Details
              </DropdownMenuItem>
              
              {currentTab !== 'cancelled' && currentTab !== 'completed' && (
                <DropdownMenuItem 
                  className="text-red-500 focus:bg-red-950/20 cursor-pointer py-2"
                  onClick={() => {
                    if(confirm("Are you sure you want to cancel this order?")) {
                      onUpdateStatus(order.id, 'cancelled');
                    }
                  }}
                >
                  <XCircle className="mr-2 h-4 w-4" /> Cancel Order
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

        </div>
      </CardHeader>
      
      {/* Items Preview */}
      <CardContent className="p-4 pt-3 bg-zinc-900/10">
        <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Package className="h-3 w-3" />
            <span>
              {order.order_items?.map(i => `${i.quantity}x ${i.product_variants?.products?.name || "Item"}`).join(", ").slice(0, 60)}
              {(order.order_items?.length || 0) > 1 ? "..." : ""}
            </span>
        </div>
      </CardContent>
    </Card>
  );
}