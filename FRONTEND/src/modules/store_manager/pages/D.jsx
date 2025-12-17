import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Package, 
  AlertTriangle, 
  ArrowRight,
  Clock,
  ArrowDownToLine,
  Truck,
  Store,
  MapPin,
  MoreHorizontal
} from "lucide-react";
import { supabase } from '@/lib/supabaseClient';

// --- UI COMPONENTS ---
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";

// using shared supabase client

export default function StoreDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  
  // Dynamic Store Context
  const [store, setStore] = useState(null);

  const [stats, setStats] = useState({
    pendingOrders: 0,
    lowStockCount: 0,
    totalItems: 0
  });

  const [lowStockItems, setLowStockItems] = useState([]);
  const [recentOrders, setRecentOrders] = useState([]);

  // --- 1. INITIALIZE DASHBOARD ---
  useEffect(() => {
    const initDashboard = async () => {
      try {
        setLoading(true);

        // inside useEffect...      
        // A. FETCH STORE CONTEXT (Dynamic)
        // In a real app, this comes from the logged-in user's assigned store.
        // For now, we grab the first active store found in DB.
        const { data: storeData, error: storeError } = await supabase
          .from("fulfillment_locations")
          .select("id, name, code, city")
          .eq("type", "store")
          .limit(1)
          .maybeSingle();

        if (storeError || !storeData) throw new Error("No Active Store Found");
        setStore(storeData);

        // // inside useEffect...

        // // OLD WAY (Bad): Fetched random store
        // // const { data: storeData } = await supabase.from("fulfillment_locations").limit(1)...

        // // NEW WAY (Good): Read the user's selection
        // const activeStoreId = localStorage.getItem("activeStoreId");

        // if (!activeStoreId) {
        // // Fallback: If no selection, fetch the first one
        // const { data } = await supabase.from("fulfillment_locations").limit(1).single();
        // if(data) localStorage.setItem("activeStoreId", data.id);
        // }

        // // Now use activeStoreId for all your queries
        // const { data: storeData } = await supabase
        // .from("fulfillment_locations")
        // .select("*")
        // .eq("id", activeStoreId) // <--- THIS IS THE KEY CHANGE
        // .single();

        // B. FETCH METRICS (Scoped to this Store)
        const storeId = storeData.id;

        // 1. Pending Orders
        // Note: Ensure your 'orders' table has 'store_id' populated, otherwise remove the .eq filter
        const { count: pendingCount } = await supabase
          .from("orders")
          .select("*", { count: 'exact', head: true })
          .eq("status", "pending"); 
          // .eq("store_id", storeId); // Uncomment if you link orders to specific 

        // 2. Total Inventory Items
        const { count: inventoryCount } = await supabase
          .from("inventory")
          .select("*", { count: 'exact', head: true })
          .eq("fulfillment_location_id", storeId);

        // 3. Low Stock Items
        const { data: lowStockData } = await supabase
          .from("inventory")
          .select(`
            id,
            quantity_on_hand,
            low_stock_threshold,
            product_variants (
              sku,
              color_name,
              size_label,
              image_url,
              products ( name )
            )
          `)
          .eq("fulfillment_location_id", storeId)
          .lt("quantity_on_hand", 10) // Threshold < 10
          .order("quantity_on_hand", { ascending: true })
          .limit(5);

        // 4. Recent Orders
        const { data: orderData } = await supabase
          .from("orders")
          .select("id, status, total_amount, created_at, type, user_id")
          .eq("status", "pending")
          .order("created_at", { ascending: false })
          .limit(5);

        // Update State
        setStats({
          pendingOrders: pendingCount || 0,
          lowStockCount: lowStockData?.length || 0,
          totalItems: inventoryCount || 0
        });

        setLowStockItems(lowStockData || []);
        setRecentOrders(orderData || []);

      } catch (error) {
        console.error("Dashboard Error:", error);
      } finally {
        setLoading(false);
      }
    };

    initDashboard();
  }, []);

  // Format Currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
  };

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-8 font-sans space-y-8">
      
      {/* --- HEADER --- */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-zinc-900">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Store Dashboard</h2>
          <div className="flex items-center gap-2 text-zinc-400 text-sm">
            {loading ? (
              <Skeleton className="h-4 w-40 bg-zinc-900" />
            ) : (
              <>
                <Store className="h-4 w-4 text-emerald-500" />
                <span className="font-medium text-zinc-200">{store?.name || "Unknown Store"}</span>
                <span className="text-zinc-600">•</span>
                <Badge variant="outline" className="text-xs border-zinc-800 text-zinc-500 font-mono">
                  {store?.code || "NO-CODE"}
                </Badge>
                <div className="flex items-center gap-1 ml-2 text-zinc-500">
                   <MapPin className="h-3 w-3" /> {store?.city}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex gap-3">
          <Button 
            variant="outline" 
            className="border-zinc-800 bg-zinc-950 text-zinc-400 hover:text-white hover:bg-zinc-900 h-10"
            onClick={() => navigate("/store-manager/inward")}
          >
            <ArrowDownToLine className="mr-2 h-4 w-4" /> Inward Stock
          </Button>
          <Button 
            className="bg-emerald-600 text-white hover:bg-emerald-700 h-10 shadow-[0_0_20px_rgba(5,150,105,0.2)]"
            onClick={() => navigate("/store-manager/orders")}
          >
            <Truck className="mr-2 h-4 w-4" /> Process Orders
          </Button>
        </div>
      </div>

      {/* --- STATS GRID --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard 
          title="Pending Orders" 
          value={stats.pendingOrders} 
          icon={Clock} 
          trend="Awaiting Action" 
          isAlert={stats.pendingOrders > 0}
          loading={loading}
        />
        <StatsCard 
          title="Critical Low Stock" 
          value={stats.lowStockCount} 
          icon={AlertTriangle} 
          trend="SKUs need restock" 
          isAlert={stats.lowStockCount > 0}
          alertColor="text-amber-500"
          borderColor="border-amber-900/30"
          loading={loading}
        />
        <StatsCard 
          title="Total Inventory" 
          value={stats.totalItems} 
          icon={Package} 
          trend="Active SKUs on shelf" 
          loading={loading}
        />
      </div>

      {/* --- CONTENT SPLIT --- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* LEFT: RECENT ORDERS */}
        <Card className="bg-zinc-950/50 backdrop-blur-sm border-zinc-800 shadow-sm flex flex-col">
          <CardHeader className="border-b border-zinc-900/80 py-4 flex flex-row items-center justify-between">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Clock className="h-4 w-4 text-emerald-500" /> Incoming Orders
            </CardTitle>
            <Button variant="link" onClick={() => navigate("/store-manager/orders")} className="text-xs text-zinc-500 hover:text-white h-auto p-0">
              View All <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            {loading ? (
               <div className="p-6 space-y-4">
                 {[1,2,3].map(i => <Skeleton key={i} className="h-14 w-full bg-zinc-900 rounded-lg" />)}
               </div>
            ) : recentOrders.length === 0 ? (
               <div className="h-64 flex flex-col items-center justify-center text-zinc-500 text-sm">
                  <Package className="h-10 w-10 mb-3 opacity-20" />
                  All caught up! No pending orders.
               </div>
            ) : (
              <div className="divide-y divide-zinc-900/80">
                {recentOrders.map((order) => (
                  <div key={order.id} className="p-4 flex items-center justify-between hover:bg-zinc-900/60 transition-colors group">
                    <div className="flex gap-4 items-center">
                       {/* Icon Box */}
                       <div className="h-10 w-10 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 group-hover:text-emerald-500 group-hover:border-emerald-900/50 transition-colors">
                          <Truck className="h-5 w-5" />
                       </div>
                       
                       <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-white">Order #{order.id.slice(0, 4)}</span>
                            {order.type === 'pickup' && <Badge variant="secondary" className="text-[9px] px-1 h-4 bg-blue-950 text-blue-400 border-blue-900">PICKUP</Badge>}
                          </div>
                          <p className="text-xs text-zinc-500 mt-0.5">
                            {new Date(order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} • <span className="text-zinc-300 font-medium">{formatCurrency(order.total_amount)}</span>
                          </p>
                       </div>
                    </div>
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button size="icon" variant="ghost" className="h-8 w-8 text-zinc-500 hover:text-white">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="bg-zinc-950 border-zinc-800 text-white">
                        <DropdownMenuItem onClick={() => navigate("/store-manager/orders")}>Quick Pack</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => navigate("/store-manager/orders")}>View Details</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* RIGHT: LOW STOCK ALERTS */}
        <Card className="bg-zinc-950/50 backdrop-blur-sm border-zinc-800 shadow-sm flex flex-col">
          <CardHeader className="border-b border-zinc-900/80 py-4 flex flex-row items-center justify-between">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" /> Low Stock Warning
            </CardTitle>
            <Button variant="link" onClick={() => navigate("/store-manager/list?filter=low")} className="text-xs text-zinc-500 hover:text-white h-auto p-0">
              Manage Inventory <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            <Table>
              <TableHeader className="bg-zinc-900/30">
                <TableRow className="border-zinc-800 hover:bg-transparent">
                  <TableHead className="text-zinc-500 h-9 text-[10px] uppercase font-bold tracking-wider w-[50%] pl-4">Product</TableHead>
                  <TableHead className="text-zinc-500 h-9 text-[10px] uppercase font-bold tracking-wider text-right pr-4">Health</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                   <TableRow><TableCell colSpan={2} className="text-center p-6 text-zinc-500">Loading Inventory...</TableCell></TableRow>
                ) : lowStockItems.length === 0 ? (
                   <TableRow><TableCell colSpan={2} className="text-center h-64 text-zinc-500 text-sm">Everything looks good.</TableCell></TableRow>
                ) : (
                  lowStockItems.map((item) => {
                    // Calculate visual health (e.g., 2/10 = 20%)
                    const health = Math.min((item.quantity_on_hand / 10) * 100, 100);
                    
                    return (
                      <TableRow key={item.id} className="border-zinc-900/50 hover:bg-zinc-900/30">
                        <TableCell className="py-3 pl-4">
                          <div className="flex flex-col">
                            <span className="text-sm text-zinc-200 font-medium truncate max-w-[180px]">
                              {item.product_variants?.products?.name}
                            </span>
                            <span className="text-xs text-zinc-500">
                               {item.product_variants?.size_label} • {item.product_variants?.color_name}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right py-3 pr-4">
                          <div className="flex flex-col items-end gap-1">
                             <div className="text-sm font-bold font-mono text-amber-500">
                               {item.quantity_on_hand} <span className="text-[10px] text-zinc-600 font-sans">UNITS</span>
                             </div>
                             {/* Mini Progress Bar */}
                             <div className="w-16 h-1 bg-zinc-800 rounded-full overflow-hidden">
                               <div 
                                 className="h-full bg-amber-500 rounded-full" 
                                 style={{ width: `${health}%` }}
                               />
                             </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}

// --- STATS CARD COMPONENT ---
function StatsCard({ title, value, icon: Icon, trend, isAlert, alertColor = "text-emerald-500", borderColor, loading }) {
  return (
    <div className={`
      relative overflow-hidden p-6 rounded-xl border bg-zinc-950/80 backdrop-blur-md transition-all duration-300
      ${isAlert ? (borderColor || 'border-zinc-800') : 'border-zinc-900 hover:border-zinc-800'}
    `}>
      {/* Background Glow for Alerts */}
      {isAlert && (
        <div className={`absolute -right-10 -top-10 h-32 w-32 rounded-full opacity-10 blur-3xl ${alertColor.replace('text-', 'bg-')}`} />
      )}

      <div className="relative z-10 flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-zinc-400">{title}</p>
        <div className={`p-2 rounded-lg bg-zinc-900/80 border border-zinc-800/50 ${isAlert ? alertColor : 'text-zinc-500'}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      
      {loading ? (
        <Skeleton className="h-9 w-20 bg-zinc-900" />
      ) : (
        <div className="relative z-10 flex items-baseline gap-2">
          <span className="text-4xl font-bold text-white tracking-tight">{value}</span>
        </div>
      )}
      
      <p className="relative z-10 text-xs text-zinc-500 mt-2 font-medium flex items-center gap-1">
        {isAlert && <AlertTriangle className="h-3 w-3" />}
        {trend}
      </p>
    </div>
  );
}