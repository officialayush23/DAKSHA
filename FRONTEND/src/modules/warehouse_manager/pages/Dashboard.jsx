import React, { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import api from "@/lib/apiClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Boxes, TrendingDown, Truck, Activity, Loader2 } from "lucide-react";

export default function WarehouseDashboard() {
  const { warehouseId } = useOutletContext();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!warehouseId) return;
    const fetchStats = async () => {
      try {
        const res = await api.get(`/admin/warehouse/dashboard/${warehouseId}`);
        setStats(res.data);
      } catch (error) {
        console.error("Dashboard error", error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [warehouseId]);

  if (loading) return <div className="p-10 flex justify-center"><Loader2 className="animate-spin text-red-500"/></div>;

  return (
    <div className="space-y-6 animate-in fade-in">
      <h2 className="text-2xl font-bold text-white">Facility Overview</h2>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard 
          title="Total SKUs" 
          value={stats?.total_skus || 0} 
          icon={Boxes} 
          desc="Distinct items in stock"
        />
        <StatsCard 
          title="Capacity Used" 
          value={`${stats?.capacity_utilization || 0}%`} 
          icon={Activity} 
          desc="Storage utilization"
          color="text-emerald-500"
        />
        <StatsCard 
          title="Pending Shipments" 
          value={stats?.pending_shipments || 0} 
          icon={Truck} 
          desc="Orders awaiting dispatch"
          color="text-amber-500"
        />
        <StatsCard 
          title="Low Stock Alerts" 
          value={stats?.low_stock_count || 0} 
          icon={TrendingDown} 
          desc="Items below threshold"
          color="text-red-500"
        />
      </div>
    </div>
  );
}

function StatsCard({ title, value, icon: Icon, desc, color = "text-zinc-200" }) {
  return (
    <Card className="bg-zinc-900 border-zinc-800">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-zinc-400">{title}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        <p className="text-xs text-zinc-500 mt-1">{desc}</p>
      </CardContent>
    </Card>
  );
}