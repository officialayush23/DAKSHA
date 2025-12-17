// src/modules/store_manager/pages/StoreDashboard.jsx

import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import api from '@/lib/apiClient'; 
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Package, ShoppingCart, AlertTriangle, Loader2, TrendingUp, MapPin, Store } from "lucide-react";

export default function StoreManagerDashboard() {
  const { store_id, store_name, store_code } = useOutletContext(); 
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      if (!store_id) return;

      setLoading(true);
      try {
        // Calls the FIXED backend endpoint
        const res = await api.get(`/admin/inventory/dashboard/${store_id}`, {
          params: { include_graphs: false } 
        });
        setStats(res.data);
      } catch (error) {
        console.error("Dashboard Load Failed:", error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, [store_id]);

  if (!store_id) {
    return (
      <div className="h-screen flex items-center justify-center text-zinc-500">
          <div className="text-center">
              <Store className="h-10 w-10 mx-auto mb-2 opacity-50"/>
              <p>Please select a store to view dashboard.</p>
          </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      
      {/* HEADER */}
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-bold tracking-tight text-white">Store Dashboard</h2>
        <div className="flex items-center gap-2 text-zinc-400">
          <MapPin className="h-4 w-4 text-emerald-500" />
          <span>Overview for <span className="font-semibold text-white">{store_name}</span></span>
          {store_code && <span className="text-xs bg-zinc-800 px-2 py-0.5 rounded text-zinc-300">{store_code}</span>}
        </div>
      </div>

      {/* STATS GRID */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        
        {/* Total Inventory */}
        <Card className="bg-zinc-950 border-zinc-800 text-white shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Total Inventory</CardTitle>
            <Package className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_items || 0}</div>
            <p className="text-xs text-zinc-500">Unique SKUs in stock</p>
          </CardContent>
        </Card>

        {/* Low Stock Alerts */}
        <Card className="bg-zinc-950 border-zinc-800 text-white shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Low Stock</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${stats?.low_stock_count > 0 ? 'text-amber-500' : 'text-zinc-500'}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats?.low_stock_count > 0 ? 'text-amber-500' : 'text-white'}`}>
                {stats?.low_stock_count || 0}
            </div>
            <p className="text-xs text-zinc-500">Items below threshold</p>
          </CardContent>
        </Card>

        {/* Pending Orders */}
        <Card className="bg-zinc-950 border-zinc-800 text-white shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Pending Orders</CardTitle>
            <ShoppingCart className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-400">{stats?.pending_orders || 0}</div>
            <p className="text-xs text-zinc-500">Awaiting fulfillment</p>
          </CardContent>
        </Card>

        {/* Revenue */}
        <Card className="bg-zinc-950 border-zinc-800 text-white shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Today's Revenue</CardTitle>
            <Activity className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">₹{stats?.todays_revenue?.toLocaleString() || 0}</div>
            <div className="flex items-center text-xs text-emerald-600/80 mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                <span>+0% from yesterday</span>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}