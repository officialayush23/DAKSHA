import React, { useState, useEffect } from 'react';
import { AdminService } from '@/lib/adminApi';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription,
  CardFooter 
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { 
  Search, 
  Package, 
  MapPin, 
  Truck, 
  Loader2, 
  AlertCircle,
  Calendar,
  User,
  ShoppingBag,
  DollarSign,
  CreditCard,
  Phone,
  Mail,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  Download,
  Eye,
  RefreshCw,
  Filter,
  MoreHorizontal,
  Store as StoreIcon,
  Home,
  Navigation,
  Archive,
  ExternalLink,
  BarChart
} from 'lucide-react';
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";

export default function Orders() {
  const [searchQuery, setSearchQuery] = useState("");
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingOrders, setLoadingOrders] = useState(true);

  const [draftStatus, setDraftStatus] = useState("");
  const [draftDescription, setDraftDescription] = useState("");
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  
  // Status options based on database schema

  const orderStatuses = [
    { value: "created", label: "Created", color: "bg-gray-500", description: "Order placed" },
    { value: "confirmed", label: "Confirmed", color: "bg-blue-500", description: "Payment successful & confirmed" },
    { value: "packed", label: "Packed", color: "bg-yellow-500", description: "Order packed and ready" },
    { value: "shipped", label: "Shipped", color: "bg-purple-500", description: "Sent for delivery" },
    { value: "ready_for_pickup", label: "Ready for Pickup", color: "bg-orange-500", description: "Waiting at store" },
    { value: "delivered", label: "Delivered", color: "bg-green-500", description: "Delivered successfully" },
    { value: "cancelled", label: "Cancelled", color: "bg-red-500", description: "Order cancelled" }
  ];

  // --- 1. Fetch All Orders ---
  const fetchOrders = async () => {
    try {
      setLoadingOrders(true);
      setError(null);
      
      // Use the new delivery orders endpoint
      const ordersData = await AdminService.getDeliveryOrders();
      
      if (Array.isArray(ordersData)) {
        setOrders(ordersData);
        toast.success(`Loaded ${ordersData.length} orders`);
      } else {
        setOrders([]);
      }
      
    } catch (err) {
      console.error("Failed to fetch orders:", err);
      setError("Failed to load orders. Please try again.");
      toast.error("Failed to load orders");
    } finally {
      setLoadingOrders(false);
    }
  };

  // --- 2. Search Order by ID ---
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setError("Please enter an order ID");
      toast.error("Please enter an order ID");
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedOrder(null);

    try {
      // Use the new delivery order detail endpoint
      const order = await AdminService.getDeliveryOrderDetail(searchQuery.trim());
      setSelectedOrder(order);
      
      // Add to recent orders if not already in list
      if (order && !orders.find(o => o.id === order.id)) {
        setOrders(prev => [order, ...prev.slice(0, 9)]);
      }
      
      toast.success("Order found");
    } catch (err) {
      setError("Order not found or access denied.");
      toast.error("Order not found");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // --- 3. Update Order Status ---
 const handleStatusUpdate = async (newStatus, description = "") => {
    if (!selectedOrder) return;
    setUpdating(true);
    try {
      await AdminService.updateDeliveryOrderStatus(selectedOrder.id, { 
        status: newStatus, 
        description: description || `Status changed to ${newStatus}` 
      });
      
      const updatedOrder = { 
        ...selectedOrder, 
        status: newStatus,
        updated_at: new Date().toISOString()
      };
      
      setSelectedOrder(updatedOrder);
      setOrders(prev => prev.map(order => 
        order.id === selectedOrder.id ? updatedOrder : order
      ));
      
      // Reset description after successful update
      setDraftDescription(""); 
      setError(null);
      toast.success(`Order status updated to ${newStatus}`);
    } catch (err) {
      setError(`Failed to update: ${err.message}`);
      toast.error("Failed to update status");
      console.error(err);
    } finally {
      setUpdating(false);
    }
  };

  // --- 4. Initialize ---
  useEffect(() => {
    fetchOrders();
  }, []);

  // --- 5. Filter Orders ---
  const filteredOrders = orders.filter(order => {
    const matchesSearch = 
      order.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.user_id?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = 
      statusFilter === "all" || 
      order.status?.toLowerCase() === statusFilter.toLowerCase();
    
    const matchesTab = 
      activeTab === "all" ||
      (activeTab === "active" && !['delivered', 'cancelled'].includes(order.status)) ||
      (activeTab === "delivered" && order.status === 'delivered') ||
      (activeTab === "pending" && order.status === 'confirmed'); // ⬅️ FIXED: 'confirmed' instead of 'processing'
    
    return matchesSearch && matchesStatus && matchesTab;
  });

  // --- 6. Get Status Info ---
  const getStatusInfo = (status) => {
    const statusInfo = orderStatuses.find(s => s.value === status?.toLowerCase());
    return statusInfo || { value: status, label: status, color: "bg-gray-500", description: "Unknown status" };
  };

  // Calculate statistics
  const totalOrders = orders.length;
  const pendingOrders = orders.filter(o => o.status === 'processing').length;
  const deliveredOrders = orders.filter(o => o.status === 'delivered').length;
  const cancelledOrders = orders.filter(o => o.status === 'cancelled').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Delivery Orders</h1>
          <p className="text-muted-foreground">Track, update, and manage delivery orders</p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchOrders} disabled={loadingOrders}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loadingOrders ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
            <ShoppingBag className="w-5 h-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalOrders}</div>
            <p className="text-xs text-muted-foreground mt-1">
              All delivery orders
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="w-5 h-5 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-500">{pendingOrders}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Awaiting processing
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Delivered</CardTitle>
            <CheckCircle className="w-5 h-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-500">{deliveredOrders}</div>
            <Progress value={(deliveredOrders / totalOrders) * 100} className="mt-2 h-2" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Cancelled</CardTitle>
            <XCircle className="w-5 h-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-500">{cancelledOrders}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Cancelled orders
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Tabs */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search Form */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input 
                    placeholder="Search by Order ID..." 
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button type="submit" disabled={loading}>
                  {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                  Search
                </Button>
              </div>
            </form>
            
            {/* Filters */}
            <div className="flex items-center gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  {orderStatuses.map(status => (
                    <SelectItem key={status.value} value={status.value}>
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${status.color}`}></div>
                        {status.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Alert variant="destructive" className="animate-in fade-in duration-200">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Orders List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <div className="flex items-center justify-between">
                  <TabsList>
                    <TabsTrigger value="all">All Orders</TabsTrigger>
                    <TabsTrigger value="active">Active</TabsTrigger>
                    <TabsTrigger value="pending">Pending</TabsTrigger>
                    <TabsTrigger value="delivered">Delivered</TabsTrigger>
                  </TabsList>
                  <span className="text-sm text-muted-foreground">
                    {filteredOrders.length} order{filteredOrders.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </Tabs>
            </CardHeader>
            <CardContent className="p-0">
              {loadingOrders ? (
                <div className="flex justify-center items-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : filteredOrders.length === 0 ? (
                <div className="text-center py-12">
                  <ShoppingBag className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                  <h3 className="text-lg font-medium mb-2">No orders found</h3>
                  <p className="text-muted-foreground">
                    {orders.length === 0 ? "No delivery orders in the system" : "Try adjusting your search or filters"}
                  </p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order ID</TableHead>
                      <TableHead>User ID</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredOrders.map((order) => (
                      <TableRow 
                        key={order.id} 
                        className={`cursor-pointer hover:bg-muted/50 ${selectedOrder?.id === order.id ? 'bg-muted' : ''}`}
                        onClick={() => {
                          // 👇 FIXED: Reset draft states when clicking a new order
                          setSelectedOrder(order);
                          setDraftStatus(order.status);
                          setDraftDescription("");
                        }}
                      >
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <div className="p-1 rounded bg-blue-100 dark:bg-blue-900/30">
                              <ShoppingBag className="h-3 w-3 text-blue-600 dark:text-blue-400" />
                            </div>
                            <span className="font-mono text-xs">{order.id.slice(0, 8)}...</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="font-medium font-mono text-sm">{order.user_id?.slice(0, 8) || 'N/A'}...</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            {order.created_at ? new Date(order.created_at).toLocaleDateString() : 'N/A'}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {order.created_at ? new Date(order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : ''}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            className={`${getStatusInfo(order.status).color} text-white gap-1`}
                          >
                            <div className="w-2 h-2 rounded-full bg-white/80"></div>
                            {getStatusInfo(order.status).label}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => setSelectedOrder(order)}>
                                <Eye className="mr-2 h-4 w-4" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(order.id)}>
                                <FileText className="mr-2 h-4 w-4" />
                                Copy Order ID
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-destructive"
                                onClick={() => handleStatusUpdate('cancelled', 'Order cancelled by admin')}
                              >
                                <XCircle className="mr-2 h-4 w-4" />
                                Cancel Order
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Order Details Sidebar */}
        <div className="space-y-6">
          {selectedOrder ? (
            <>
              {/* Order Summary */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Order Details</span>
                    <Badge className={getStatusInfo(selectedOrder.status).color + " text-white"}>
                      {getStatusInfo(selectedOrder.status).label}
                    </Badge>
                  </CardTitle>
                  <CardDescription className="flex items-center gap-2">
                    <Calendar className="h-3 w-3" />
                    {selectedOrder.created_at ? new Date(selectedOrder.created_at).toLocaleDateString() : 'Date not available'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Order Info */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Order ID:</span>
                      <span className="font-mono text-xs">{selectedOrder.id}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">User ID:</span>
                      <span className="font-mono text-xs">{selectedOrder.user_id || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Created:</span>
                      <span>{selectedOrder.created_at ? new Date(selectedOrder.created_at).toLocaleString() : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Updated:</span>
                      <span>{selectedOrder.updated_at ? new Date(selectedOrder.updated_at).toLocaleString() : 'N/A'}</span>
                    </div>
                  </div>

                  <Separator />

                  {/* Status Update */}
                  <div className="space-y-3">
                    <Label>Update Order Status</Label>
                    <Select 
                      value={draftStatus} // ⬅️ Bound to draft status
                      onValueChange={setDraftStatus} // ⬅️ Updates local state, doesn't fire API yet
                      disabled={updating}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        {orderStatuses.map((status) => (
                          <SelectItem key={status.value} value={status.value}>
                            <div className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full ${status.color}`}></div>
                              {status.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Textarea 
                      placeholder="Add status description or notes..."
                      className="text-sm"
                      rows={2}
                      value={draftDescription} // ⬅️ Bound to state
                      onChange={(e) => setDraftDescription(e.target.value)} // ⬅️ Bound to state
                    />
                    
                    <Button 
                      className="w-full"
                      onClick={() => handleStatusUpdate(draftStatus, draftDescription)} // ⬅️ Fires API with draft data!
                      disabled={updating || !draftStatus}
                    >
                      {updating ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle className="mr-2 h-4 w-4" />
                      )}
                      Update Status
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button 
                    variant="outline" 
                    className="w-full justify-start"
                    onClick={() => navigator.clipboard.writeText(selectedOrder.id)}
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Copy Order ID
                  </Button>
                  <Button 
                    variant="destructive" 
                    className="w-full justify-start"
                    onClick={() => handleStatusUpdate('cancelled', 'Order cancelled by admin')}
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Cancel Order
                  </Button>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Order Details</CardTitle>
                <CardDescription>Select an order to view details</CardDescription>
              </CardHeader>
              <CardContent className="text-center py-12">
                <ShoppingBag className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <p className="text-muted-foreground">Select an order from the list or search for an order ID</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}