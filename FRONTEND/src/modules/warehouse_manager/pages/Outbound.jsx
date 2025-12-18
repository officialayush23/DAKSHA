//  FRONTEND/src/modules/warehouse_manager/pages/Outbound.jsx

import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  Truck, PackageCheck, Clock, MapPin, ChevronDown, ChevronUp, Box, Loader2, CheckCircle
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function Outbound() {
  const { warehouse_id } = useOutletContext();
  
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [expandedOrder, setExpandedOrder] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  // --- FETCH ORDERS ---
  const fetchOrders = async () => {
    if (!warehouse_id) return;
    setLoading(true);
    try {
      const res = await api.get(`/admin/warehouse/outbound/orders/${warehouse_id}`);
      setOrders(res.data || []);
    } catch (error) {
      toast.error("Failed to load orders");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [warehouse_id]);

  // --- SHIP ACTION ---
  const handleShip = async (orderId) => {
    if(!confirm("Confirm shipment dispatch?")) return;
    
    setProcessingId(orderId);
    try {
        await api.post(`/admin/warehouse/outbound/ship/${orderId}`, null, {
            params: { warehouse_id }
        });
        toast.success("Order marked as Shipped!");
        // Remove from list locally
        setOrders(prev => prev.filter(o => o.id !== orderId));
    } catch (error) {
        toast.error("Failed to update status");
    } finally {
        setProcessingId(null);
    }
  };

  const toggleExpand = (id) => {
      setExpandedOrder(expandedOrder === id ? null : id);
  };

  if (!warehouse_id) return null;

  return (
    <div className="w-full space-y-6 animate-in fade-in">
      
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
          <Truck className="h-8 w-8 text-orange-500" /> Outbound Orders
        </h2>
        <p className="text-zinc-400 text-sm">Pick, Pack, and Ship allocated orders.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* STATS SUMMARY (Optional) */}
          <Card className="bg-zinc-950 border-zinc-800 text-white lg:col-span-3">
              <div className="flex divide-x divide-zinc-800">
                  <div className="flex-1 p-4 flex items-center gap-4">
                      <div className="p-3 rounded-full bg-blue-500/10 text-blue-500"><Clock className="h-5 w-5"/></div>
                      <div>
                          <p className="text-2xl font-bold text-white">{orders.length}</p>
                          <p className="text-xs text-zinc-500 uppercase">Pending Dispatch</p>
                      </div>
                  </div>
                  <div className="flex-1 p-4 flex items-center gap-4">
                      <div className="p-3 rounded-full bg-emerald-500/10 text-emerald-500"><PackageCheck className="h-5 w-5"/></div>
                      <div>
                          <p className="text-2xl font-bold text-white">0</p>
                          <p className="text-xs text-zinc-500 uppercase">Completed Today</p>
                      </div>
                  </div>
              </div>
          </Card>

          {/* ORDER LIST */}
          <div className="lg:col-span-3 space-y-4">
              {loading ? (
                  <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
                      <Loader2 className="h-8 w-8 animate-spin mb-2"/> Loading orders...
                  </div>
              ) : orders.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-64 border border-dashed border-zinc-800 rounded-xl text-zinc-500">
                      <Box className="h-10 w-10 opacity-20 mb-2"/>
                      <p>No pending orders assigned to this warehouse.</p>
                  </div>
              ) : (
                  orders.map(order => (
                      <Card key={order.id} className="bg-zinc-950 border-zinc-800 text-white overflow-hidden transition-all duration-200 hover:border-zinc-700">
                          <div 
                            className="p-4 flex flex-col md:flex-row items-center justify-between gap-4 cursor-pointer bg-zinc-900/20"
                            onClick={() => toggleExpand(order.id)}
                          >
                              {/* Order Info */}
                              <div className="flex items-center gap-4 flex-1">
                                  <div className={`p-2 rounded-full ${order.status === 'pending' ? 'bg-amber-500/10 text-amber-500' : 'bg-blue-500/10 text-blue-500'}`}>
                                      <Box className="h-5 w-5" />
                                  </div>
                                  <div>
                                      <div className="flex items-center gap-2">
                                          <h4 className="font-mono font-medium text-white">#{order.id.slice(0,8)}</h4>
                                          <Badge variant="outline" className="border-zinc-700 text-zinc-400 capitalize">{order.status}</Badge>
                                      </div>
                                      <div className="flex items-center gap-1 text-xs text-zinc-500 mt-1">
                                          <Clock className="h-3 w-3" /> {new Date(order.created_at).toLocaleString()}
                                      </div>
                                  </div>
                              </div>

                              {/* Customer/Address */}
                              <div className="flex-1 hidden md:block">
                                  <p className="text-sm text-zinc-300 flex items-center gap-2">
                                      <MapPin className="h-3 w-3 text-zinc-500"/>
                                      {/* Mock address if delivery_address_id is just UUID in this view */}
                                      Delivery Address ID: {order.delivery_address_id ? order.delivery_address_id.slice(0,8) : 'N/A'}...
                                  </p>
                              </div>

                              {/* Actions */}
                              <div className="flex items-center gap-3">
                                  {expandedOrder === order.id ? <ChevronUp className="h-4 w-4 text-zinc-500"/> : <ChevronDown className="h-4 w-4 text-zinc-500"/>}
                              </div>
                          </div>

                          {/* EXPANDED CONTENT (PICK LIST) */}
                          {expandedOrder === order.id && (
                              <div className="border-t border-zinc-900 bg-black/50 p-4 animate-in slide-in-from-top-2">
                                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                      {/* Items List */}
                                      <div className="lg:col-span-2 space-y-3">
                                          <h5 className="text-xs font-semibold uppercase text-zinc-500 tracking-wider mb-2">Picking Manifest</h5>
                                          <ScrollArea className="h-[200px] pr-4">
                                              {order.items.map((item, idx) => (
                                                  <div key={idx} className="flex items-center justify-between p-3 rounded bg-zinc-900 border border-zinc-800 mb-2">
                                                      <div className="flex items-center gap-3">
                                                          <div className="h-8 w-8 rounded bg-black border border-zinc-800 flex items-center justify-center text-xs font-bold text-zinc-500">
                                                              {item.quantity}x
                                                          </div>
                                                          <div>
                                                              <p className="text-sm font-medium text-white">{item.product_variants?.products?.name || "Product"}</p>
                                                              <p className="text-xs text-zinc-500 font-mono">{item.product_variants?.sku}</p>
                                                          </div>
                                                      </div>
                                                      <CheckCircle className="h-4 w-4 text-zinc-700 hover:text-emerald-500 cursor-pointer transition-colors" />
                                                  </div>
                                              ))}
                                          </ScrollArea>
                                      </div>

                                      {/* Actions Panel */}
                                      <div className="flex flex-col justify-between border-l border-zinc-900 pl-6">
                                          <div className="space-y-1">
                                              <p className="text-xs text-zinc-500 uppercase">Total Items</p>
                                              <p className="text-xl font-bold text-white">{order.items.reduce((acc, i) => acc + i.quantity, 0)} units</p>
                                          </div>
                                          
                                          <div className="space-y-3 mt-4">
                                              <Button 
                                                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
                                                onClick={() => handleShip(order.id)}
                                                disabled={processingId === order.id}
                                              >
                                                  {processingId === order.id ? <Loader2 className="animate-spin h-4 w-4 mr-2"/> : <Truck className="h-4 w-4 mr-2"/>}
                                                  Dispatch Order
                                              </Button>
                                              <Button variant="outline" className="w-full border-zinc-800 text-zinc-400 hover:text-white">
                                                  Print Label
                                              </Button>
                                          </div>
                                      </div>
                                  </div>
                              </div>
                          )}
                      </Card>
                  ))
              )}
          </div>
      </div>
    </div>
  );
}