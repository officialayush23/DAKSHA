import React, { useEffect, useState } from "react";
import { 
  Activity, 
  CreditCard, 
  DollarSign, 
  Package, 
  AlertTriangle,
  ArrowUpRight
} from "lucide-react";
import { inventoryService } from "@/services/inventoryService";
import { Link } from "react-router-dom";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function StoreDashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);

  // Hardcoded Store ID (In reality, get from Auth Context)
  const MY_STORE_ID = "store-123-uuid";

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        // const res = await inventoryService.getStoreDashboard(MY_STORE_ID);
        // setDashboardData(res.data);
        
        // --- MOCK DATA (Simulating API Response) ---
        setTimeout(() => {
          setDashboardData({
            totalRevenue: 45231.89,
            activeOrders: 12,
            lowStockCount: 4,
            recentSales: [
              { id: "ORD-001", customer: "Liam Johnson", amount: 250.00, status: "Completed" },
              { id: "ORD-002", customer: "Olivia Smith", amount: 120.50, status: "Processing" },
              { id: "ORD-003", customer: "Noah Williams", amount: 350.00, status: "Processing" },
            ],
            lowStockItems: [
              { sku: "SKU-992", name: "Cotton T-Shirt (M)", qty: 2 },
              { sku: "SKU-881", name: "Denim Jeans (32)", qty: 0 },
              { sku: "SKU-774", name: "Running Shoes (10)", qty: 3 },
            ]
          });
          setLoading(false);
        }, 800);
      } catch (error) {
        console.error("Failed to load dashboard", error);
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="flex flex-col gap-6">
      {/* 1. Key Metrics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${dashboardData?.totalRevenue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">+20.1% from last month</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Orders</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">+{dashboardData?.activeOrders}</div>
            <p className="text-xs text-muted-foreground">+180.1% from last hour</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Stock Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{dashboardData?.lowStockCount}</div>
            <p className="text-xs text-muted-foreground">Items need attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stock Efficiency</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">98.2%</div>
            <p className="text-xs text-muted-foreground">+4% from last week</p>
          </CardContent>
        </Card>
      </div>

      {/* 2. Main Content Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        
        {/* Recent Sales (Left - Wider) */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Sales</CardTitle>
            <CardDescription>You made 265 sales this month.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">Order</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboardData?.recentSales.map((sale) => (
                  <TableRow key={sale.id}>
                    <TableCell className="font-medium">{sale.id}</TableCell>
                    <TableCell>{sale.customer}</TableCell>
                    <TableCell>
                      <Badge variant={sale.status === "Completed" ? "outline" : "secondary"}>
                        {sale.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">${sale.amount}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Low Stock Alerts (Right - Narrower) */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Low Stock Alerts</CardTitle>
            <CardDescription>Re-stock these items immediately.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData?.lowStockItems.map((item, index) => (
                <div key={index} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                  <div className="flex items-center gap-4">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-orange-100">
                      <Package className="h-4 w-4 text-orange-600" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm font-medium leading-none">{item.name}</p>
                      <p className="text-xs text-muted-foreground">{item.sku}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-destructive">{item.qty} left</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Button asChild className="w-full" variant="outline">
                <Link to="/inventory/stock">
                  Manage Inventory <ArrowUpRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Loading State Component
function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-[120px] rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-7">
        <Skeleton className="col-span-4 h-[400px] rounded-xl" />
        <Skeleton className="col-span-3 h-[400px] rounded-xl" />
      </div>
    </div>
  );
}
