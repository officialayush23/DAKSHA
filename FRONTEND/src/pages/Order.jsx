import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "@/lib/apiClient";
import { format } from "date-fns";
import { toast } from "sonner";
import { 
  ArrowLeft, 
  Package, 
  RotateCcw, 
  ShoppingBag, 
  Truck, 
  Search, 
  Loader2, 
  AlertCircle 
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

// --- Helper: Status Colors ---
const getStatusColor = (status) => {
  const s = status?.toLowerCase() || "";
  switch (s) {
    case 'pending': return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case 'processing': return "bg-blue-100 text-blue-800 border-blue-200";
    case 'shipped': return "bg-indigo-100 text-indigo-800 border-indigo-200";
    case 'delivered': return "bg-green-100 text-green-800 border-green-200";
    case 'cancelled': return "bg-red-100 text-red-800 border-red-200";
    case 'returned': return "bg-orange-100 text-orange-800 border-orange-200";
    default: return "bg-gray-100 text-gray-800 border-gray-200";
  }
};

export default function OrdersPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("active");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- Fetch Orders from API ---
  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        // GET /orders/history
        const { data } = await api.get("/orders/history");
        
        // Ensure data is an array
        setOrders(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to fetch orders:", err);
        setError("Could not load your order history. Please try again.");
        toast.error("Failed to load orders.");
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  // Filter orders based on status
  const activeOrders = orders.filter(o => 
    ['pending', 'processing', 'shipped', 'out_for_delivery'].includes(o.status)
  );
  
  const pastOrders = orders.filter(o => 
    ['delivered', 'cancelled', 'returned', 'refunded'].includes(o.status)
  );

  if (loading) return <OrdersSkeleton />;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <AlertCircle className="h-10 w-10 text-red-500" />
        <p className="text-lg font-medium text-muted-foreground">{error}</p>
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto py-6 px-4 space-y-6">
      
      {/* Header */}
      <div className="flex items-center gap-4 mb-2">
        <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">My Orders</h1>
      </div>

      <Tabs defaultValue="active" className="w-full" onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="active">Active ({activeOrders.length})</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="buy-again">Buy Again</TabsTrigger>
        </TabsList>

        {/* --- ACTIVE ORDERS TAB --- */}
        <TabsContent value="active" className="space-y-4 min-h-[400px]">
          {activeOrders.length === 0 ? (
            <EmptyState message="No active orders found." subMessage="Looks like you're all caught up!" />
          ) : (
            activeOrders.map((order) => <OrderCard key={order.id} order={order} />)
          )}
        </TabsContent>

        {/* --- HISTORY TAB --- */}
        <TabsContent value="history" className="space-y-4 min-h-[400px]">
          <div className="relative mb-4">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input type="search" placeholder="Search past orders..." className="pl-8 bg-background" />
          </div>
          {pastOrders.length === 0 ? (
            <EmptyState message="No past orders found." subMessage="Your purchase history will appear here." />
          ) : (
            pastOrders.map((order) => <OrderCard key={order.id} order={order} />)
          )}
        </TabsContent>

        {/* --- BUY AGAIN TAB --- */}
        <TabsContent value="buy-again" className="min-h-[400px]">
           <BuyAgainList orders={orders} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// --- Sub-Components ---

function OrderCard({ order }) {
  // Safe date parsing
  const dateStr = order.created_at ? format(new Date(order.created_at), "MMM d, yyyy • h:mm a") : "Date N/A";
  
  // Calculate Item Count (if items exist)
  const items = order.items || []; // Assuming backend returns joined items
  const itemCount = items.reduce((acc, item) => acc + (item.quantity || 1), 0);

  return (
    <Card className="overflow-hidden border-border/60 hover:shadow-sm transition-shadow">
      <CardHeader className="bg-muted/30 pb-3 pt-4 border-b border-border/40">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm">Order #{order.id.slice(0, 8).toUpperCase()}</span>
              <span className="text-xs text-muted-foreground">• {dateStr}</span>
            </div>
          </div>
          <Badge variant="outline" className={`${getStatusColor(order.status)} font-medium border`}>
            {order.status?.toUpperCase() || "UNKNOWN"}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-4 pb-4 space-y-4">
        {/* Render Items */}
        {items.length > 0 ? (
          <div className="space-y-3">
            {items.map((item) => (
              <div key={item.id} className="flex gap-4">
                <div className="h-16 w-16 bg-muted rounded-md flex items-center justify-center shrink-0 border border-border/50">
                  {/* If you have item images, use <img /> here */}
                  <Package className="h-6 w-6 text-muted-foreground/40" />
                </div>
                <div className="flex-1 min-w-0 flex flex-col justify-center">
                  <p className="font-medium text-sm truncate">{item.product_name || "Product Name"}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.variant_name ? `Variant: ${item.variant_name}` : "Standard"}
                  </p>
                  <div className="flex justify-between items-center mt-1">
                    <p className="text-xs text-muted-foreground">Qty: {item.quantity}</p>
                    {/* Fallback to price_at_purchase if available */}
                    <p className="font-medium text-sm">₹{(item.price_at_purchase || 0).toFixed(2)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground italic py-2">No items details available.</p>
        )}

        <Separator />
        
        <div className="flex justify-between items-center text-sm">
          <span className="text-muted-foreground">Total ({itemCount} items)</span>
          <span className="font-bold text-base">₹{Number(order.total_amount).toFixed(2)}</span>
        </div>
      </CardContent>

      <CardFooter className="bg-muted/10 p-3 flex gap-3">
        {order.status === 'delivered' ? (
           <>
             <Button variant="outline" size="sm" className="flex-1 text-xs h-9">
               <RotateCcw className="mr-2 h-3.5 w-3.5" /> Return / Exchange
             </Button>
             <Button size="sm" className="flex-1 text-xs h-9">
               <ShoppingBag className="mr-2 h-3.5 w-3.5" /> Buy Again
             </Button>
           </>
        ) : (
           <Button className="w-full text-xs h-9" size="sm" variant="secondary">
             <Truck className="mr-2 h-3.5 w-3.5" /> Track Package
           </Button>
        )}
      </CardFooter>
    </Card>
  );
}

function BuyAgainList({ orders }) {
  // Logic: Flatten items -> Deduplicate by Product ID
  const allItems = orders.flatMap(o => o.items || []);
  
  // Deduplicate based on product_variant_id or product_name
  const uniqueItemsMap = new Map();
  allItems.forEach(item => {
    if (!uniqueItemsMap.has(item.product_variant_id)) {
      uniqueItemsMap.set(item.product_variant_id, item);
    }
  });
  const uniqueItems = Array.from(uniqueItemsMap.values());

  if (uniqueItems.length === 0) {
    return <EmptyState message="No purchase history yet." subMessage="Buy something to see it here!" />;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
      {uniqueItems.map((item, idx) => (
        <Card key={item.id || idx} className="group cursor-pointer hover:shadow-md transition-all overflow-hidden border-border/60">
          <div className="aspect-square bg-muted flex items-center justify-center relative">
            <Package className="h-10 w-10 text-muted-foreground/30" />
            <Button size="icon" className="absolute bottom-2 right-2 h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity rounded-full shadow-sm">
              <ShoppingBag className="h-4 w-4" />
            </Button>
          </div>
          <div className="p-3">
            <h3 className="font-medium text-sm truncate">{item.product_name || "Product"}</h3>
            <p className="text-xs text-muted-foreground mb-2 truncate">
              {item.variant_name || "One Size"}
            </p>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-sm">₹{(item.price_at_purchase || 0).toFixed(0)}</span>
              <span className="text-[10px] text-blue-600 font-medium">Add +</span>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

function EmptyState({ message, subMessage }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground bg-muted/10 rounded-lg border border-dashed">
      <div className="bg-background p-4 rounded-full mb-4 shadow-sm">
        <Package className="h-8 w-8 text-muted-foreground/50" />
      </div>
      <h3 className="font-medium text-foreground">{message}</h3>
      <p className="text-sm mt-1 mb-4 max-w-xs mx-auto">{subMessage}</p>
      <Button variant="outline" asChild size="sm">
        <Link to="/products">Browse Catalog</Link>
      </Button>
    </div>
  );
}

function OrdersSkeleton() {
  return (
    <div className="container max-w-4xl mx-auto py-6 px-4 space-y-6">
      <div className="flex items-center gap-4 mb-6">
         <Skeleton className="h-8 w-8 rounded-full" />
         <Skeleton className="h-8 w-48" />
      </div>
      <Skeleton className="h-10 w-full mb-6" />
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border rounded-lg p-4 space-y-4">
            <div className="flex justify-between">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-6 w-20" />
            </div>
            <div className="flex gap-4">
              <Skeleton className="h-16 w-16 rounded-md" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}