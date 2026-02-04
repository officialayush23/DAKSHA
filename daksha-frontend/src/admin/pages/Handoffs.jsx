import React, { useEffect, useState } from 'react';
import { AdminService } from '@/lib/adminApi';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  ArrowRightLeft, 
  Users, 
  Clock, 
  Loader2, 
  RefreshCw, 
  Search,
  Eye,
  Truck,
  Package,
  Store,
  User,
  Calendar,
  Download,
  CheckCircle,
  AlertCircle,
  Clock as ClockIcon,
  MapPin,
  Phone,
  Mail,
  Hash,
  Tag,
  Building,
  Navigation,
  CalendarDays,
  PhoneCall,
  FileText
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";

export default function Handoffs() {
  const [handoffs, setHandoffs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedHandoff, setSelectedHandoff] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [stores, setStores] = useState([]);

  // Status options based on API
  const STATUS_OPTIONS = ['all', 'pending', 'in_progress', 'completed', 'cancelled'];
  const HANDOFF_TYPES = ['pickup', 'delivery', 'transfer', 'return'];

  // --- Fetch Data ---
  const fetchHandoffs = async () => {
    try {
      setLoading(true);
      
      // Fetch stores first
      const storesData = await AdminService.listStores();
      const storesList = Array.isArray(storesData) ? storesData : [];
      setStores(storesList);
      
      // Try to fetch handoffs from API
      // First, let's try the actual handoffs endpoint
      try {
        const handoffsData = await fetchWithAuth('/admin/handoffs');
        if (handoffsData && Array.isArray(handoffsData)) {
          setHandoffs(handoffsData);
          return;
        }
      } catch (error) {
        console.log('Handoffs endpoint not available or empty, trying alternative');
      }
      
      // If handoffs endpoint fails, try to get data from pickups
      if (storesList.length > 0) {
        const allPickups = [];
        
        // Fetch pickups for each store
        for (const store of storesList.slice(0, 5)) { // Limit to first 5 stores
          try {
            const pickups = await AdminService.listStorePickups(store.id);
            if (Array.isArray(pickups)) {
              const storePickups = pickups.map(pickup => ({
                ...pickup,
                store_id: store.id,
                store_name: store.name,
                store_city: store.city,
                store_state: store.state,
                type: 'pickup',
                status: pickup.status || 'pending'
              }));
              allPickups.push(...storePickups);
            }
          } catch (error) {
            console.error(`Failed to fetch pickups for store ${store.id}:`, error);
          }
        }
        
        setHandoffs(allPickups);
      }
      
    } catch (error) {
      console.error("Failed to fetch handoff logs:", error);
      toast.error("Failed to load handoffs");
      setHandoffs([]);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to fetch with auth
  const fetchWithAuth = async (endpoint) => {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const { data: sessionData } = await supabase.auth.getSession();
    const token = sessionData?.session?.access_token;
    
    const response = await fetch(`${baseURL}${endpoint}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return await response.json();
  };

  useEffect(() => {
    fetchHandoffs();
  }, []);

  // Helper for Status Badge
  const getStatusBadge = (status) => {
    switch(status?.toLowerCase()) {
      case 'completed': 
      case 'delivered':
        return (
          <Badge className="bg-green-600 hover:bg-green-700">
            <CheckCircle className="w-3 h-3 mr-1" />
            Completed
          </Badge>
        );
      case 'pending': 
      case 'created':
        return (
          <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200">
            <ClockIcon className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        );
      case 'cancelled': 
      case 'failed':
        return (
          <Badge className="bg-red-600 hover:bg-red-700">
            <AlertCircle className="w-3 h-3 mr-1" />
            Cancelled
          </Badge>
        );
      case 'in_progress': 
      case 'in_transit':
      case 'processing':
        return (
          <Badge className="bg-blue-600 hover:bg-blue-700">
            <Truck className="w-3 h-3 mr-1" />
            In Progress
          </Badge>
        );
      default: 
        return <Badge variant="outline">{status || 'Unknown'}</Badge>;
    }
  };

  // Helper for Type Badge
  const getTypeBadge = (type) => {
    const typeMap = {
      'pickup': { label: 'Pickup', color: 'bg-blue-100 text-blue-800' },
      'delivery': { label: 'Delivery', color: 'bg-green-100 text-green-800' },
      'transfer': { label: 'Transfer', color: 'bg-purple-100 text-purple-800' },
      'return': { label: 'Return', color: 'bg-orange-100 text-orange-800' },
      'order_pickup': { label: 'Order Pickup', color: 'bg-indigo-100 text-indigo-800' },
      'inventory_transfer': { label: 'Inventory Transfer', color: 'bg-teal-100 text-teal-800' }
    };
    
    const config = typeMap[type] || { label: type, color: 'bg-gray-100 text-gray-800' };
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  // Filter handoffs
  const filteredHandoffs = handoffs.filter(handoff => {
    const matchesSearch = 
      handoff.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      handoff.store_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (handoff.agent_name && handoff.agent_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (handoff.delivery_person && handoff.delivery_person.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (handoff.order_id && handoff.order_id.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = filterStatus === 'all' || handoff.status === filterStatus;
    
    return matchesSearch && matchesStatus;
  });

  // Calculate statistics
  const calculateStats = () => {
    const stats = {
      total: handoffs.length,
      completed: handoffs.filter(h => 
        h.status === 'completed' || h.status === 'delivered'
      ).length,
      pending: handoffs.filter(h => 
        h.status === 'pending' || h.status === 'created'
      ).length,
      in_progress: handoffs.filter(h => 
        h.status === 'in_progress' || h.status === 'in_transit' || h.status === 'processing'
      ).length,
      cancelled: handoffs.filter(h => 
        h.status === 'cancelled' || h.status === 'failed'
      ).length,
      uniqueStores: new Set(handoffs.map(h => h.store_id)).size
    };
    
    return stats;
  };

  const stats = calculateStats();

  // View handoff details
  const viewHandoffDetails = (handoff) => {
    setSelectedHandoff(handoff);
    setViewDialogOpen(true);
  };

  // Update handoff status
  const updateHandoffStatus = async (handoffId, newStatus) => {
    try {
      // Check if this is a pickup
      if (selectedHandoff?.type === 'pickup') {
        await AdminService.updatePickup(handoffId, { status: newStatus });
        toast.success("Pickup status updated");
      } else if (selectedHandoff?.order_id) {
        // Check if it's an order
        await AdminService.updateDelivery(selectedHandoff.order_id, { status: newStatus });
        toast.success("Order status updated");
      }
      
      fetchHandoffs(); // Refresh data
      setViewDialogOpen(false);
    } catch (error) {
      console.error("Failed to update status:", error);
      toast.error("Failed to update status");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Handoffs & Transfers</h1>
          <p className="text-muted-foreground">Monitor inventory transfers, pickups, and deliveries</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchHandoffs} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Handoffs</CardTitle>
            <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">
              Across {stats.uniqueStores} stores
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.in_progress}</div>
            <div className="text-xs text-muted-foreground">
              Currently active
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            <div className="text-xs text-muted-foreground">
              {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}% success rate
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
            <div className="text-xs text-muted-foreground">
              {stats.cancelled} cancelled
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by ID, store name, agent, or order..."
              className="pl-9"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        <div className="flex gap-2">
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Handoff Table */}
      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID / Reference</TableHead>
              <TableHead>Store</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center">
                  <div className="flex justify-center items-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin" /> 
                    Loading handoff logs...
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredHandoffs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <Truck className="h-8 w-8 mb-2 opacity-50" />
                    <p>No handoff events found</p>
                    <p className="text-sm">
                      {handoffs.length === 0 
                        ? "No data available. Check if pickups exist in stores." 
                        : "Try adjusting your search or filters"}
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredHandoffs.slice(0, 50).map((handoff) => (
                <TableRow key={handoff.id || handoff.pickup_id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-mono text-xs truncate max-w-[120px]" title={handoff.id}>
                        {handoff.id ? handoff.id.substring(0, 8) + '...' : 'N/A'}
                      </div>
                      {handoff.order_id && (
                        <div className="text-xs text-muted-foreground">
                          Order: {handoff.order_id.substring(0, 8)}...
                        </div>
                      )}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1">
                        <Store className="h-3 w-3" />
                        <span className="font-medium">{handoff.store_name || 'Unknown Store'}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {handoff.store_city || ''} {handoff.store_state || ''}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      <div>{getTypeBadge(handoff.type)}</div>
                      {handoff.quantity && (
                        <div className="text-xs text-muted-foreground flex items-center gap-1">
                          <Package className="h-3 w-3" />
                          {handoff.quantity} items
                        </div>
                      )}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      <div className="text-sm">
                        {handoff.created_at ? format(new Date(handoff.created_at), 'MMM dd, hh:mm a') : "N/A"}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {handoff.created_at ? formatDistanceToNow(new Date(handoff.created_at), { addSuffix: true }) : ""}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    {getStatusBadge(handoff.status)}
                  </TableCell>
                  
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8"
                      onClick={() => viewHandoffDetails(handoff)}
                      title="View Details"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* View Details Dialog */}
      {selectedHandoff && (
        <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Handoff Details</DialogTitle>
              <DialogDescription>
                ID: <span className="font-mono text-xs">{selectedHandoff.id || 'N/A'}</span>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-muted-foreground">Status</Label>
                  <div className="mt-1">{getStatusBadge(selectedHandoff.status)}</div>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Type</Label>
                  <div className="mt-1">{getTypeBadge(selectedHandoff.type)}</div>
                </div>
              </div>

              {/* Store Details */}
              <div className="space-y-2">
                <Label className="text-sm font-semibold flex items-center gap-2">
                  <Store className="h-4 w-4" /> Store Details
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">Store Name</Label>
                    <p className="font-medium">{selectedHandoff.store_name || 'Unknown Store'}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Store ID</Label>
                    <p className="font-mono text-sm">{selectedHandoff.store_id || 'N/A'}</p>
                  </div>
                  {(selectedHandoff.store_city || selectedHandoff.store_state) && (
                    <div className="col-span-2">
                      <Label className="text-xs text-muted-foreground">Location</Label>
                      <p className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {selectedHandoff.store_city || ''} {selectedHandoff.store_state || ''}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Pickup/Delivery Details */}
              <div className="space-y-2">
                <Label className="text-sm font-semibold flex items-center gap-2">
                  <Truck className="h-4 w-4" /> Transfer Details
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedHandoff.order_id && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Order ID</Label>
                      <p className="font-mono text-sm">{selectedHandoff.order_id}</p>
                    </div>
                  )}
                  {selectedHandoff.quantity && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Quantity</Label>
                      <p>{selectedHandoff.quantity} items</p>
                    </div>
                  )}
                  {selectedHandoff.delivery_person && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Delivery Person</Label>
                      <p>{selectedHandoff.delivery_person}</p>
                    </div>
                  )}
                  {selectedHandoff.agent_name && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Agent Name</Label>
                      <p>{selectedHandoff.agent_name}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Timestamps */}
              <div className="space-y-2">
                <Label className="text-sm font-semibold flex items-center gap-2">
                  <CalendarDays className="h-4 w-4" /> Timestamps
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {selectedHandoff.created_at && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Created At</Label>
                      <p>{format(new Date(selectedHandoff.created_at), 'PPP pp')}</p>
                    </div>
                  )}
                  {selectedHandoff.updated_at && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Updated At</Label>
                      <p>{format(new Date(selectedHandoff.updated_at), 'PPP pp')}</p>
                    </div>
                  )}
                  {selectedHandoff.created_at && (
                    <div className="col-span-2">
                      <Label className="text-xs text-muted-foreground">Relative Time</Label>
                      <p>{formatDistanceToNow(new Date(selectedHandoff.created_at), { addSuffix: true })}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Notes */}
              {selectedHandoff.notes && (
                <div className="space-y-2">
                  <Label className="text-sm font-semibold flex items-center gap-2">
                    <FileText className="h-4 w-4" /> Notes
                  </Label>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-3">
                    <p className="text-sm whitespace-pre-line">{selectedHandoff.notes}</p>
                  </div>
                </div>
              )}

              {/* Status Update Actions */}
              {selectedHandoff.status && selectedHandoff.status !== 'completed' && selectedHandoff.status !== 'cancelled' && (
                <div className="space-y-2">
                  <Label className="text-sm font-semibold">Update Status</Label>
                  <div className="flex gap-2">
                    {selectedHandoff.status === 'pending' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => updateHandoffStatus(selectedHandoff.id, 'in_progress')}
                      >
                        Mark as In Progress
                      </Button>
                    )}
                    {selectedHandoff.status === 'in_progress' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => updateHandoffStatus(selectedHandoff.id, 'completed')}
                      >
                        Mark as Completed
                      </Button>
                    )}
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => updateHandoffStatus(selectedHandoff.id, 'cancelled')}
                    >
                      Cancel Handoff
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* API Info */}
      <div className="text-sm text-muted-foreground p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <AlertCircle className="h-4 w-4" />
          <span className="font-medium">API Information</span>
        </div>
        <p>Currently using:</p>
        <ul className="list-disc pl-5 mt-1 space-y-1">
          <li>Stores API: <code className="text-xs">/admin/stores</code></li>
          <li>Store Pickups: <code className="text-xs">/admin/stores/&#123;id&#125;/pickups</code></li>
        </ul>
      </div>
    </div>
  );
}