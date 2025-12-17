// src/modules/store_manager/pages/HistoryLog.jsx

import React, { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom"; // 1. Use Context
import api from "@/lib/apiClient"; // 2. Use API Client
import { 
  History, Search, Filter, FileText, Calendar, Store, ArrowUpRight
} from "lucide-react";
import { format } from "date-fns";

// --- UI COMPONENTS ---
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

export default function HistoryLogs() {
  const { store_id, store_name } = useOutletContext();
  
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // --- FETCH HISTORICAL DATA ---
  useEffect(() => {
    const fetchHistory = async () => {
      if (!store_id) return;

      setLoading(true);
      try {
        // REUSE EXISTING API: We fetch 'completed' and 'cancelled' orders
        // We make two parallel requests to get the full history
        const [completedRes, cancelledRes] = await Promise.all([
          api.get(`/admin/inventory/orders/${store_id}`, { params: { tab: 'completed' } }),
          api.get(`/admin/inventory/orders/${store_id}`, { params: { tab: 'cancelled' } })
        ]);

        const completedOrders = completedRes.data || [];
        const cancelledOrders = cancelledRes.data || [];

        // Combine and sort by date (newest first)
        const allHistory = [...completedOrders, ...cancelledOrders].sort((a, b) => 
          new Date(b.created_at) - new Date(a.created_at)
        );

        setLogs(allHistory);

      } catch (err) {
        console.error("History Error:", err);
        toast.error("Failed to load history.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [store_id]);

  // --- FILTERING ---
  const filteredLogs = logs.filter(log => {
    const searchLower = searchQuery.toLowerCase();
    
    // Safety check for user_id since users table might not be joined if RLS blocks it
    const customerName = log.user_id || "Guest"; 

    const matchesSearch = 
      log.id.toLowerCase().includes(searchLower) ||
      customerName.toLowerCase().includes(searchLower);
    
    const matchesStatus = statusFilter === "all" || log.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  // --- HELPER: STATUS BADGE ---
  const getStatusBadge = (status) => {
    switch (status) {
      case 'shipped':
        return <Badge className="bg-blue-950 text-blue-400 border-blue-900">Shipped</Badge>;
      case 'delivered':
        return <Badge className="bg-emerald-950 text-emerald-400 border-emerald-900">Delivered</Badge>;
      case 'cancelled':
        return <Badge className="bg-red-950 text-red-400 border-red-900">Cancelled</Badge>;
      case 'returned':
        return <Badge className="bg-amber-950 text-amber-400 border-amber-900">Returned</Badge>;
      default:
        return <Badge variant="outline" className="text-zinc-500">{status}</Badge>;
    }
  };

  if (!store_id) {
    return (
        <div className="h-screen flex items-center justify-center text-zinc-500">
            <div className="text-center">
                <Store className="h-10 w-10 mx-auto mb-2 opacity-50"/>
                <p>Please select a store to view history.</p>
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
            <History className="h-8 w-8 text-emerald-500" />
            History Logs
          </h2>
          <div className="flex items-center gap-2 mt-2 text-sm text-zinc-400">
             <Store className="h-4 w-4" />
             <span>Archive for: <span className="text-white font-medium">{store_name}</span></span>
          </div>
        </div>
        <div>
          <Button variant="outline" className="border-zinc-800 text-zinc-400 hover:text-white bg-black">
            <FileText className="mr-2 h-4 w-4" /> Export CSV
          </Button>
        </div>
      </div>

      {/* TOOLBAR */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
          <Input 
            placeholder="Search Order ID or Customer ID..." 
            className="pl-9 bg-black border-zinc-800 text-white h-10 focus:border-emerald-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px] bg-black border-zinc-800 text-white">
            <Filter className="mr-2 h-4 w-4 text-zinc-500" />
            <SelectValue placeholder="Filter Status" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
            <SelectItem value="all">All Events</SelectItem>
            <SelectItem value="shipped">Shipped</SelectItem>
            <SelectItem value="delivered">Delivered</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* LOGS TABLE */}
      <Card className="bg-zinc-950 border-zinc-800 shadow-sm">
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-zinc-900/50">
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-500 font-bold uppercase text-xs w-[180px]">Timestamp</TableHead>
                <TableHead className="text-zinc-500 font-bold uppercase text-xs">Reference ID</TableHead>
                <TableHead className="text-zinc-500 font-bold uppercase text-xs">Customer ID</TableHead>
                <TableHead className="text-zinc-500 font-bold uppercase text-xs">Status</TableHead>
                <TableHead className="text-zinc-500 font-bold uppercase text-xs text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                    Loading archives...
                  </TableCell>
                </TableRow>
              ) : filteredLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                    No history found matching your filters.
                  </TableCell>
                </TableRow>
              ) : (
                filteredLogs.map((log) => (
                  <TableRow key={log.id} className="border-zinc-900 hover:bg-zinc-900/30 group">
                    
                    {/* TIMESTAMP */}
                    <TableCell className="text-zinc-400 text-xs font-mono">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-3 w-3 text-zinc-600" />
                        {format(new Date(log.created_at), "MMM d, yyyy")}
                        <span className="text-zinc-600">|</span>
                        {format(new Date(log.created_at), "h:mm a")}
                      </div>
                    </TableCell>

                    {/* REFERENCE ID */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                         <span className="font-mono text-white text-sm">#{log.id.slice(0, 8).toUpperCase()}</span>
                         <ArrowUpRight className="h-3 w-3 text-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <span className="block text-[10px] text-zinc-600 uppercase mt-0.5">{log.type} Order</span>
                    </TableCell>

                    {/* CUSTOMER */}
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-zinc-300 text-xs font-mono">{log.user_id?.slice(0,12)}...</span>
                      </div>
                    </TableCell>

                    {/* STATUS */}
                    <TableCell>
                      {getStatusBadge(log.status)}
                    </TableCell>

                    {/* VALUE */}
                    <TableCell className="text-right font-mono text-zinc-300">
                      ₹{log.total_amount}
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