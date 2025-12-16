import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom"; // <--- IMPORT THIS
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  Package, Truck, Check, Loader2, Clock, ShoppingBag, Hash
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";

export default function FulfillmentQueue() {
  const { locationId } = useOutletContext(); // <--- GET ID FROM LAYOUT
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [processingId, setProcessingId] = useState(null);

  const fetchQueue = async () => {
    if (!locationId) return; // Wait for location to be selected
    
    try {
      setLoading(true);
      // Pass source_id to the API
      const res = await api.get("/admin/fulfillment/queue", {
        params: { source_id: locationId }
      });
      setOrders(res.data || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load queue.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 30000);
    return () => clearInterval(interval);
  }, [locationId]); // Re-fetch when location changes

  const handleAction = async (orderId, action, trackingNum = "") => {
    setProcessingId(orderId);
    try {
      await api.post(`/admin/fulfillment/process/${orderId}`, null, { 
        params: { 
            action,
            source_id: locationId, // Pass ID for security check
            tracking_number: trackingNum || `TRK-${orderId.slice(0,8).toUpperCase()}`
        }
      });
      
      if (action === 'ship') {
        toast.success("Order Shipped!");
        setOrders(prev => prev.filter(o => o.id !== orderId));
      } else {
        toast.info("Picking started");
        setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: 'processing' } : o));
      }
    } catch (error) {
      toast.error("Action failed.");
    } finally {
      setProcessingId(null);
    }
  };

  if (!locationId) return <div className="p-10 text-center text-zinc-500">Select a location from the sidebar.</div>;

  return (
    <div className="w-full space-y-6 animate-in fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShoppingBag className="h-8 w-8 text-amber-500" /> Active Queue
          </h2>
          <p className="text-zinc-400">Processing orders for location: <span className="text-amber-500 font-mono">{locationId.slice(0,8)}</span></p>
        </div>
        <Button onClick={fetchQueue} variant="outline" className="border-zinc-800 text-zinc-400 hover:text-white">
          Refresh List
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-amber-500"/></div>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed border-zinc-800 rounded-xl bg-zinc-950/30 text-zinc-500">
          <Check className="h-12 w-12 mb-4 text-emerald-500/50" />
          <h3 className="text-lg font-medium text-white">All Caught Up!</h3>
          <p>No orders pending for this location.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <AnimatePresence>
            {orders.map((order) => (
              <OrderCard 
                key={order.id} 
                order={order} 
                onAction={handleAction} 
                isProcessing={processingId === order.id}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

function OrderCard({ order, onAction, isProcessing }) {
  const [tracking, setTracking] = useState("");
  const totalItems = order.order_items?.length || 0;
  
  return (
    <motion.div layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <Card className={`bg-zinc-950 border-zinc-800 flex flex-col h-full transition-all ${order.status === 'processing' ? 'border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.1)]' : ''}`}>
        <CardHeader className="p-4 pb-3">
          <div className="flex justify-between items-start mb-2">
             <div className="flex flex-col">
                <span className="text-[10px] uppercase text-zinc-500 font-bold">Order ID</span>
                <div className="font-mono text-xs text-white bg-zinc-900 px-2 py-1 rounded border border-zinc-800">
                  #{order.id.slice(0, 8).toUpperCase()}
                </div>
             </div>
             <Badge className={order.status === 'processing' ? 'bg-amber-600 animate-pulse' : 'bg-zinc-800 text-zinc-400'}>
                {order.status === 'processing' ? 'Picking' : 'Pending'}
             </Badge>
          </div>
        </CardHeader>
        
        <Separator className="bg-zinc-900" />

        <CardContent className="p-4 flex-1">
          <ScrollArea className="h-[150px] pr-2">
            <ul className="space-y-3">
              {order.order_items?.map((item) => (
                <li key={item.id} className="flex gap-3 text-sm">
                  <div className="h-10 w-10 bg-zinc-900 rounded border border-zinc-800 flex items-center justify-center overflow-hidden shrink-0">
                     <Package className="h-5 w-5 text-zinc-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-zinc-200 font-medium truncate">{item.product_variants?.products?.name}</p>
                    <div className="flex items-center justify-between text-xs text-zinc-500 mt-1">
                      <span>{item.product_variants?.size_label} | {item.product_variants?.color_name}</span>
                      <span className="text-amber-500 font-bold">x{item.quantity}</span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </ScrollArea>

          {order.status === 'processing' && (
            <div className="mt-4 space-y-2">
               <label className="text-[10px] uppercase text-zinc-500 font-bold flex items-center gap-1">
                 <Hash className="h-3 w-3" /> Tracking Number
               </label>
               <Input 
                 value={tracking}
                 onChange={(e) => setTracking(e.target.value)}
                 placeholder="Auto-generated if empty"
                 className="h-8 bg-black border-zinc-800 text-xs focus-visible:ring-amber-500"
               />
            </div>
          )}
        </CardContent>

        <CardFooter className="p-4 bg-zinc-900/20 border-t border-zinc-900">
          <Button 
            className={`w-full ${order.status === 'pending' ? 'bg-zinc-800 hover:bg-zinc-700' : 'bg-amber-600 hover:bg-amber-700'} text-white`} 
            onClick={() => onAction(order.id, order.status === 'pending' ? 'start_picking' : 'ship', tracking)}
            disabled={isProcessing}
          >
            {isProcessing ? <Loader2 className="animate-spin h-4 w-4 mr-2"/> : (order.status === 'pending' ? 'Start Picking' : 'Ship Order')}
          </Button>
        </CardFooter>
      </Card>
    </motion.div>
  );
}