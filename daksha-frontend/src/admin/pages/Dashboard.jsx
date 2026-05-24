import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { AdminService } from '@/lib/adminApi';
import {
  Package, Archive, TrendingUp, AlertTriangle, Store, MessageSquare,
  Tag, Loader2, RefreshCw, BarChart3, AlertCircle, MapPin, DollarSign,
  Shield, BrainCircuit, Hash,
} from 'lucide-react';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";

export default function Dashboard() {
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [training, setTraining]   = useState(false);

  const [stats, setStats] = useState({
    inventory: {
      total_stock: 0,
      reserved_stock: 0,
      total_variants: 0,
      low_stock_count: 0,
      low_stock_variants: [],
    },
    stores: [],
    complaints: [],
    offers: [],
  });

  const fetchDashboardData = async () => {
    try {
      const dashboardStats = await AdminService.getDashboardStats();
      const extractArray = (res) => Array.isArray(res) ? res : (res?.data || []);

      setStats({
        inventory: dashboardStats.inventory || {
          total_stock: 0, reserved_stock: 0,
          total_variants: 0, low_stock_count: 0, low_stock_variants: [],
        },
        stores: extractArray(dashboardStats.stores),
        complaints: extractArray(dashboardStats.complaints),
        offers: extractArray(dashboardStats.offers),
      });
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchDashboardData(); }, []);

  const handleRefresh = () => { setRefreshing(true); fetchDashboardData(); };

  const handleTrainModel = async () => {
    setTraining(true);
    try {
      await AdminService.trainModel();
      toast.success("Training started successfully");
    } catch (error) {
      toast.error("Failed to start model training");
    } finally {
      setTraining(false);
    }
  };

  const totalStores    = stats.stores.length;
  const activeStores   = stats.stores.filter(s => s.active).length;
  const openComplaints = stats.complaints.filter(c => c.status === 'open').length;
  // Coupon model uses status: 'active' | 'expired' | 'disabled' (not a boolean .active)
  const activeOffers   = stats.offers.filter(o => o.status === 'active' || o.active === true).length;
  const stockUtil      = stats.inventory.total_stock > 0
    ? Math.min(100, (stats.inventory.reserved_stock / stats.inventory.total_stock) * 100) : 0;

  const lowSkus = stats.inventory.low_stock_variants || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your store</p>
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button variant="secondary" size="sm" onClick={handleTrainModel} disabled={training} className="w-full sm:w-auto">
            {training ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <BrainCircuit className="h-4 w-4 mr-2" />}
            Train Model
          </Button>
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing} className="w-full sm:w-auto">
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} /> Refresh
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Stock</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inventory.total_stock?.toLocaleString() || 0}</div>
            <p className="text-xs text-muted-foreground">Units across all warehouses</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reserved Stock</CardTitle>
            <Archive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inventory.reserved_stock?.toLocaleString() || 0}</div>
            <div className="mt-2 space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Utilization</span>
                <span className="font-medium">{stockUtil.toFixed(1)}%</span>
              </div>
              <Progress value={stockUtil} className="h-2" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Variants</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inventory.total_variants?.toLocaleString() || 0}</div>
            <p className="text-xs text-muted-foreground">Distinct SKUs in catalog</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats.inventory.low_stock_count || 0}</div>
            <p className="text-xs text-muted-foreground">Items needing replenishment</p>
          </CardContent>
        </Card>
      </div>

      {/* SKU Low-Stock Table */}
      {lowSkus.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hash className="h-5 w-5 text-amber-500" />
              Low Stock SKUs
              <Badge variant="destructive" className="ml-2">{lowSkus.length}</Badge>
            </CardTitle>
            <CardDescription>Variants with ≤ 5 units available — replenish soon</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead>Variant</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead className="text-right">Reserved</TableHead>
                    <TableHead className="text-right">Available</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lowSkus.map((s) => (
                    <TableRow key={s.variant_id}>
                      <TableCell>
                        <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">
                          {s.sku || s.variant_id?.slice(0, 8) + '…'}
                        </code>
                      </TableCell>
                      <TableCell className="font-medium text-sm max-w-[160px] truncate">{s.name}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {[s.color, s.size].filter(Boolean).join(' / ') || '—'}
                      </TableCell>
                      <TableCell className="text-right text-sm">{s.total_stock}</TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">{s.reserved_stock}</TableCell>
                      <TableCell className="text-right font-semibold text-sm">
                        <span className={s.available_stock <= 0 ? 'text-red-600' : 'text-amber-600'}>
                          {s.available_stock}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={s.available_stock <= 0 ? 'destructive' : 'secondary'} className="text-[10px]">
                          {s.available_stock <= 0 ? 'Out of stock' : 'Low stock'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />Overview
          </TabsTrigger>
          <TabsTrigger value="stores" className="flex items-center gap-2">
            <Store className="h-4 w-4" />Stores ({totalStores})
          </TabsTrigger>
          <TabsTrigger value="support" className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />Support ({openComplaints})
          </TabsTrigger>
          <TabsTrigger value="offers" className="flex items-center gap-2">
            <Tag className="h-4 w-4" />Offers ({activeOffers})
          </TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Stores Summary</CardTitle><CardDescription>Physical store locations</CardDescription></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Total Stores</span>
                    <Badge>{totalStores}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Active Stores</span>
                    <Badge variant={activeStores === totalStores ? "default" : "secondary"}>{activeStores}/{totalStores}</Badge>
                  </div>
                  <Progress value={totalStores ? (activeStores / totalStores) * 100 : 0} className="h-2" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Support Summary</CardTitle><CardDescription>Customer complaints</CardDescription></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Total Complaints</span>
                    <Badge>{stats.complaints.length}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Open Complaints</span>
                    <Badge variant={openComplaints === 0 ? "default" : "destructive"}>{openComplaints}</Badge>
                  </div>
                  <Progress value={stats.complaints.length > 0 ? ((stats.complaints.length - openComplaints) / stats.complaints.length) * 100 : 100} className="h-2" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Stores */}
        <TabsContent value="stores">
          <Card>
            <CardHeader><CardTitle>Store Locations</CardTitle><CardDescription>All your physical stores</CardDescription></CardHeader>
            <CardContent>
              {stats.stores.length > 0 ? (
                <div className="space-y-3">
                  {stats.stores.map((store) => (
                    <div key={store.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Store className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{store.name}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <MapPin className="h-3 w-3" />{store.city}, {store.state}
                        </div>
                      </div>
                      <Badge variant={store.active ? "default" : "secondary"}>
                        {store.active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Store className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">No stores found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Support */}
        <TabsContent value="support">
          <Card>
            <CardHeader><CardTitle>Customer Complaints</CardTitle></CardHeader>
            <CardContent>
              {stats.complaints.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stats.complaints.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell className="max-w-xs truncate">{c.description}</TableCell>
                        <TableCell>
                          <Badge variant={c.status === 'open' ? 'destructive' : 'secondary'}>{c.status}</Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {new Date(c.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8">
                  <Shield className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">No complaints found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Offers */}
        <TabsContent value="offers">
          <Card>
            <CardHeader><CardTitle>Promotional Offers</CardTitle></CardHeader>
            <CardContent>
              {stats.offers.length > 0 ? (
                <div className="space-y-3">
                  {stats.offers.map((offer) => (
                    <div key={offer.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Tag className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{offer.name}</span>
                        </div>
                        <Badge variant={offer.active ? "default" : "secondary"}>{offer.active ? "Active" : "Inactive"}</Badge>
                      </div>
                      <div className="space-y-1 text-sm">
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-3 w-3" />
                          <span>{offer.discount_value}% off</span>
                        </div>
                        {offer.eligible_category && <div><span className="text-muted-foreground">Category: </span>{offer.eligible_category}</div>}
                        {offer.min_cart_value > 0 && <div><span className="text-muted-foreground">Min cart: </span>₹{offer.min_cart_value}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Tag className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">No offers found</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Store, label: "Total Stores", value: totalStores },
          { icon: Tag, label: "Active Offers", value: activeOffers },
          { icon: AlertCircle, label: "Open Issues", value: openComplaints },
          { icon: Package, label: "Low Stock", value: stats.inventory.low_stock_count || 0 },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="p-4 border rounded-lg">
            <div className="flex items-center gap-2">
              <Icon className="h-4 w-4" />
              <span className="text-sm font-medium">{label}</span>
            </div>
            <div className="text-xl font-bold mt-1">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
