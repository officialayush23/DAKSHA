import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  Truck, Package, CheckCircle, Loader2, Calendar, MapPin 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export default function OutboundOrders() {
  const { warehouseId } = useOutletContext();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [processingId, setProcessingId] = useState(null);

  const fetchOutbound = async () => {
    if (!warehouseId) return;
    setLoading(true);
    try {
      const res = await api.get(`/admin/warehouse/outbound/orders/${warehouseId}`);
      setOrders(res.data || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load outbound orders.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOutbound();
  }, [warehouseId]);

  const handleShip = async (orderId) => {
    setProcessingId(orderId);
    try {
      // Calls POST /admin/warehouse/outbound/ship/{order_id}?warehouse_id=...
      await api.post(`/admin/warehouse/outbound/ship/${orderId}`, null, {
        params: { warehouse_id: warehouseId }
      });
      
      toast.success("Order marked as Shipped!");
      setOrders((prev) => prev.filter((o) => o.id !== orderId));
    } catch (error) {
      console.error(error);
      toast.error("Shipping failed. Check console.");
    } finally {
      setProcessingId(null);
    }
  };

  if (!warehouseId) return null;

  return (
    <div className="space-y-6 animate-in fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Truck className="h-6 w-6 text-red-500" /> Outbound Shipments
          </h2>
          <p className="text-zinc-400 text-sm">Review and dispatch orders assigned to this facility.</p>
        </div>
        <Button onClick={fetchOutbound} variant="outline" className="border-zinc-800 text-zinc-400 hover:text-white">
          Refresh
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center p-20"><Loader2 className="animate-spin text-red-500 h-8 w-8" /></div>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed border-zinc-800 rounded-xl bg-zinc-900/20 text-zinc-500">
          <CheckCircle className="h-12 w-12 mb-4 text-zinc-700" />
          <h3 className="text-lg font-medium text-white">All Clear</h3>
          <p>No pending shipments for this warehouse.</p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          <AnimatePresence>
            {orders.map((order) => (
              <motion.div
                key={order.id}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
              >
                <Card className="bg-zinc-900 border-zinc-800 flex flex-col h-full hover:border-zinc-700 transition-colors">
                  <CardHeader className="p-4 pb-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <Badge variant="outline" className="font-mono text-[10px] border-zinc-700 text-zinc-400 mb-1">
                          #{order.id.slice(0, 8).toUpperCase()}
                        </Badge>
                        <CardTitle className="text-sm font-medium text-white">
                          {order.order_items?.length} Item(s)
                        </CardTitle>
                      </div>
                      <Badge className="bg-amber-900/30 text-amber-500 border-amber-900/50">
                        PENDING
                      </Badge>
                    </div>
                  </CardHeader>
                  
                  <Separator className="bg-zinc-800" />
                  
                  <CardContent className="p-4 flex-1">
                    <ScrollArea className="h-[140px] pr-2">
                      <div className="space-y-3">
                        {order.order_items?.map((item) => (
                          <div key={item.id} className="flex gap-3 text-sm">
                            <div className="h-9 w-9 bg-zinc-950 rounded border border-zinc-800 flex items-center justify-center shrink-0">
                               <Package className="h-4 w-4 text-zinc-600" />
                            </div>
                            <div>
                              <p className="text-zinc-300 font-medium line-clamp-1">
                                {item.product_variants?.products?.name || "Product"}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-zinc-500">
                                <span>{item.product_variants?.color_name}</span>
                                <span className="text-white font-bold bg-zinc-800 px-1.5 rounded">x{item.quantity}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                    
                    <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                       <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(order.created_at).toLocaleDateString()}
                       </div>
                       <div className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          Zone A
                       </div>
                    </div>
                  </CardContent>

                  <CardFooter className="p-4 bg-zinc-950/50 border-t border-zinc-800">
                    <Button 
                      className="w-full bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-900/20"
                      onClick={() => handleShip(order.id)}
                      disabled={processingId === order.id}
                    >
                      {processingId === order.id ? (
                        <Loader2 className="animate-spin h-4 w-4 mr-2" />
                      ) : (
                        <Truck className="h-4 w-4 mr-2" />
                      )}
                      Dispatch Order
                    </Button>
                  </CardFooter>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}