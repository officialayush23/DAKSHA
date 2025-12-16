import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom"; // <--- Get Context
import api from "@/lib/apiClient";
import { 
  Archive, Search, Calendar, Truck, Loader2, PackageCheck, Hash, AlertTriangle 
} from "lucide-react";
import { toast } from "sonner";

import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function FulfillmentHistory() {
  const { locationId } = useOutletContext(); // <--- Get Selected Location
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState([]);
  const [search, setSearch] = useState("");

  const fetchHistory = async () => {
    if (!locationId) return;

    setLoading(true);
    try {
      // Pass both status='history' AND source_id to backend
      const res = await api.get("/admin/fulfillment/queue", {
        params: { 
            status: "history",
            source_id: locationId
        }
      });
      setOrders(res.data || []);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load shipping history.");
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch whenever the user switches location in the sidebar
  useEffect(() => {
    fetchHistory();
  }, [locationId]);

  // Filter Logic
  const filtered = orders.filter(o => 
    o.id.toLowerCase().includes(search.toLowerCase()) ||
    o.status.toLowerCase().includes(search.toLowerCase()) ||
    o.tracking_number?.toLowerCase().includes(search.toLowerCase())
  );

  // --- EMPTY STATE IF NO LOCATION SELECTED ---
  if (!locationId) {
      return (
          <div className="flex flex-col items-center justify-center h-[50vh] text-zinc-500">
              <AlertTriangle className="h-10 w-10 mb-4 opacity-20" />
              <p>Select a location from the sidebar to view history.</p>
          </div>
      );
  }

  return (
    <div className="w-full space-y-6 animate-in fade-in">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-4 border-b border-zinc-900 pb-6">
        <div className="space-y-1">
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            <Archive className="h-8 w-8 text-amber-600" /> Shipped Archive
          </h2>
          <p className="text-zinc-400 text-sm">
            History for location: <span className="text-amber-500 font-mono">{locationId.slice(0,8)}...</span>
          </p>
        </div>
        
        <div className="relative w-full md:w-80">
           <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
           <Input 
             placeholder="Search ID, Status, or Tracking..." 
             className="pl-9 bg-zinc-950 border-zinc-800 h-10 text-white focus-visible:ring-amber-500"
             value={search}
             onChange={(e) => setSearch(e.target.value)}
           />
        </div>
      </div>

      {/* Data Table */}
      <Card className="bg-zinc-950 border-zinc-800 shadow-sm overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-zinc-900/50">
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-500 w-[140px]">Order ID</TableHead>
                <TableHead className="text-zinc-500">Status</TableHead>
                <TableHead className="text-zinc-500">Items</TableHead>
                <TableHead className="text-zinc-500">Tracking Info</TableHead>
                <TableHead className="text-zinc-500 text-right">Processed At</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto text-amber-500"/>
                  </TableCell>
                </TableRow>
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                    {search ? "No matching records found." : "No shipped orders found for this location."}
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((order) => (
                  <TableRow key={order.id} className="border-zinc-800 hover:bg-zinc-900/40 group transition-colors">
                    <TableCell className="font-mono text-xs text-zinc-400 font-medium">
                      #{order.id.slice(0, 8).toUpperCase()}
                    </TableCell>
                    <TableCell>
                      <Badge className={
                          order.status === 'delivered' 
                          ? 'bg-emerald-600/20 text-emerald-500 border-emerald-900/50' 
                          : 'bg-indigo-600/20 text-indigo-400 border-indigo-900/50'
                      }>
                        {order.status.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-zinc-300 text-sm">{order.total_items_count || 0} Items</span>
                    </TableCell>
                    <TableCell>
                       <div className="flex flex-col gap-1">
                         <div className="flex items-center gap-2 text-zinc-300 text-xs">
                           <Truck className="h-3 w-3 text-zinc-500" />
                           {order.courier_name || "Standard"}
                         </div>
                         <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-500">
                            <Hash className="h-2.5 w-2.5" />
                            {order.tracking_number || "PENDING"}
                         </div>
                       </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2 text-zinc-500 text-xs">
                        <Calendar className="h-3 w-3" />
                        {order.shipped_at 
                          ? new Date(order.shipped_at).toLocaleDateString() 
                          : new Date(order.updated_at).toLocaleDateString()}
                      </div>
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