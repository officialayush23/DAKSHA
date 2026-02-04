import React, { useEffect, useState } from 'react';
import { AdminService } from '@/lib/adminApi';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from "@/components/ui/dialog";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Loader2, 
  MoreHorizontal,
  Search,
  Filter,
  RefreshCw,
  User,
  Mail,
  Phone,
  Calendar,
  FileText,
  Tag,
  AlertTriangle,
  ThumbsUp,
  XCircle,
  Eye,
  MessageSquare,
  ShoppingBag,
  Truck,
  Package,
  CreditCard,
  MapPin,
  Download
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { format } from 'date-fns';

export default function Complaints() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  
  // Dialog State
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [resolutionNote, setResolutionNote] = useState("");
  const [newStatus, setNewStatus] = useState("resolved");
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // View details dialog
  const [viewDialogOpen, setViewDialogOpen] = useState(false);

  // Categories based on typical e-commerce complaints
  const COMPLAINT_CATEGORIES = [
    'product_quality',
    'delivery_issue',
    'payment_problem',
    'return_refund',
    'website_app',
    'customer_service',
    'pricing_billing',
    'order_cancellation',
    'damaged_item',
    'wrong_item',
    'late_delivery',
    'missing_item',
    'other'
  ];

  // Status options matching your enum schema
  const STATUS_OPTIONS = [
    { value: 'open', label: 'Open', color: 'bg-red-500' },
    { value: 'in_progress', label: 'In Progress', color: 'bg-blue-500' },
    { value: 'resolved', label: 'Resolved', color: 'bg-green-500' },
    { value: 'closed', label: 'Closed', color: 'bg-gray-500' },
    { value: 'pending', label: 'Pending', color: 'bg-yellow-500' }
  ];

  // --- 1. Fetch Complaints ---
  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const res = await AdminService.getComplaints(); // Updated to match your API
      setComplaints(Array.isArray(res) ? res : res.data || []);
    } catch (error) {
      console.error("Failed to load complaints:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  // --- 2. Handle Status Update ---
  const openUpdateDialog = (complaint) => {
    setSelectedComplaint(complaint);
    setNewStatus(complaint.status || 'open');
    setResolutionNote(complaint.resolution_notes || "");
  };

  const handleStatusUpdate = async () => {
    if (!selectedComplaint) return;
    
    setIsSubmitting(true);
    try {
      // Updated to match your API schema
      await AdminService.updateComplaint(selectedComplaint.id, {
        status: newStatus,
        resolution_notes: resolutionNote
      });
      
      // Close and Refresh
      setSelectedComplaint(null);
      fetchComplaints();
    } catch (error) {
      console.error("Failed to update complaint:", error);
      alert(error.response?.data?.message || "Error updating complaint.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- 3. View Complaint Details ---
  const viewComplaintDetails = (complaint) => {
    setSelectedComplaint(complaint);
    setViewDialogOpen(true);
  };

  // --- 4. Filter Complaints ---
  const filteredComplaints = complaints.filter(complaint => {
    const matchesSearch = 
      complaint.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      complaint.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      complaint.customer_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      complaint.customer_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      complaint.order_id?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === "all" || complaint.status === filterStatus;
    const matchesCategory = filterCategory === "all" || complaint.category === filterCategory;
    
    return matchesSearch && matchesStatus && matchesCategory;
  });

  // --- 5. Calculate Statistics ---
  const calculateStats = () => {
    const stats = {
      total: complaints.length,
      open: complaints.filter(c => c.status === 'open').length,
      in_progress: complaints.filter(c => c.status === 'in_progress').length,
      resolved: complaints.filter(c => c.status === 'resolved').length,
      closed: complaints.filter(c => c.status === 'closed').length,
      high_priority: complaints.filter(c => c.priority === 'high').length,
    };
    
    return stats;
  };

  const stats = calculateStats();

  // --- 6. Helper Functions ---
  const getStatusBadge = (status) => {
    const statusObj = STATUS_OPTIONS.find(s => s.value === status);
    if (!statusObj) return <Badge variant="outline">{status}</Badge>;
    
    return (
      <Badge className={`${statusObj.color} text-white`}>
        {status === 'open' && <AlertCircle className="w-3 h-3 mr-1" />}
        {status === 'in_progress' && <Clock className="w-3 h-3 mr-1" />}
        {status === 'resolved' && <CheckCircle2 className="w-3 h-3 mr-1" />}
        {status === 'pending' && <Clock className="w-3 h-3 mr-1" />}
        {status === 'closed' && <ThumbsUp className="w-3 h-3 mr-1" />}
        {statusObj.label}
      </Badge>
    );
  };

  const getCategoryBadge = (category) => {
    const categoryMap = {
      'product_quality': { label: 'Product Quality', color: 'bg-purple-500' },
      'delivery_issue': { label: 'Delivery Issue', color: 'bg-orange-500' },
      'payment_problem': { label: 'Payment Problem', color: 'bg-red-500' },
      'return_refund': { label: 'Return/Refund', color: 'bg-blue-500' },
      'website_app': { label: 'Website/App', color: 'bg-indigo-500' },
      'customer_service': { label: 'Customer Service', color: 'bg-pink-500' },
      'pricing_billing': { label: 'Pricing/Billing', color: 'bg-yellow-500' },
      'order_cancellation': { label: 'Order Cancellation', color: 'bg-gray-500' },
      'damaged_item': { label: 'Damaged Item', color: 'bg-red-600' },
      'wrong_item': { label: 'Wrong Item', color: 'bg-amber-500' },
      'late_delivery': { label: 'Late Delivery', color: 'bg-orange-600' },
      'missing_item': { label: 'Missing Item', color: 'bg-red-700' },
      'other': { label: 'Other', color: 'bg-gray-400' }
    };
    
    const cat = categoryMap[category] || { label: category, color: 'bg-gray-400' };
    return <Badge className={`${cat.color} text-white text-xs`}>{cat.label}</Badge>;
  };

  const getPriorityBadge = (priority) => {
    switch(priority) {
      case 'high': return <Badge variant="destructive">High Priority</Badge>;
      case 'medium': return <Badge className="bg-yellow-500">Medium Priority</Badge>;
      case 'low': return <Badge className="bg-blue-500">Low Priority</Badge>;
      default: return <Badge variant="outline">Normal</Badge>;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMM dd, yyyy hh:mm a');
    } catch {
      return dateString;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Customer Complaints</h1>
          <p className="text-muted-foreground">Manage and resolve customer issues efficiently</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchComplaints}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Complaints</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Open</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.open}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.in_progress}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Closed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats.closed}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">High Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats.high_priority}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search complaints by subject, description, email, or order ID..."
              className="pl-9"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        <div className="flex gap-2">
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              {STATUS_OPTIONS.map(status => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={filterCategory} onValueChange={setFilterCategory}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Filter by category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {COMPLAINT_CATEGORIES.map(category => (
                <SelectItem key={category} value={category}>
                  {getCategoryBadge(category).props.children}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Complaints Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID / Date</TableHead>
              <TableHead>Subject & Category</TableHead>
              <TableHead>Customer Details</TableHead>
              <TableHead>Order Details</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center">
                  <div className="flex justify-center items-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin" />
                    <span>Loading complaints...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredComplaints.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <MessageSquare className="h-8 w-8 mb-2 opacity-50" />
                    <p>No complaints found</p>
                    <p className="text-sm">Try adjusting your filters</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredComplaints.map((complaint) => (
                <TableRow key={complaint.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-mono text-xs truncate max-w-[120px]" title={complaint.id}>
                        {complaint.id.substring(0, 8)}...
                      </div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(complaint.created_at)}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">{complaint.subject || "No Subject"}</div>
                      <div className="text-sm text-muted-foreground line-clamp-1">
                        {complaint.description}
                      </div>
                      <div>
                        {complaint.category && getCategoryBadge(complaint.category)}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        <span className="text-sm">{complaint.customer_name || "Anonymous"}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Mail className="h-3 w-3" />
                        <span className="text-sm text-muted-foreground truncate max-w-[150px]">
                          {complaint.customer_email || "No email"}
                        </span>
                      </div>
                      {complaint.customer_phone && (
                        <div className="flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          <span className="text-sm text-muted-foreground">{complaint.customer_phone}</span>
                        </div>
                      )}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      {complaint.order_id ? (
                        <>
                          <div className="flex items-center gap-1">
                            <ShoppingBag className="h-3 w-3" />
                            <span className="text-sm font-mono">#{complaint.order_id.substring(0, 8)}...</span>
                          </div>
                          {complaint.order_total && (
                            <div className="text-xs text-muted-foreground">
                              ${parseFloat(complaint.order_total).toFixed(2)}
                            </div>
                          )}
                        </>
                      ) : (
                        <span className="text-sm text-muted-foreground">No order linked</span>
                      )}
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    {complaint.priority && getPriorityBadge(complaint.priority)}
                  </TableCell>
                  
                  <TableCell>
                    {getStatusBadge(complaint.status)}
                  </TableCell>
                  
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8"
                        onClick={() => viewComplaintDetails(complaint)}
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => openUpdateDialog(complaint)}>
                            <FileText className="h-4 w-4 mr-2" />
                            Update Status
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <Mail className="h-4 w-4 mr-2" />
                            Contact Customer
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <ShoppingBag className="h-4 w-4 mr-2" />
                            View Order Details
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Tag className="h-4 w-4 mr-2" />
                            Add Internal Note
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Update Status Dialog */}
      {selectedComplaint && (
        <Dialog open={!!selectedComplaint} onOpenChange={(open) => !open && setSelectedComplaint(null)}>
          <DialogContent className="sm:max-w-[550px]">
            <DialogHeader>
              <DialogTitle>Update Complaint Status</DialogTitle>
              <DialogDescription>
                Complaint ID: <span className="font-mono text-xs">{selectedComplaint.id}</span>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Current Status: {getStatusBadge(selectedComplaint.status)}</Label>
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-status">Update Status</Label>
                <Select value={newStatus} onValueChange={setNewStatus}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map(status => (
                      <SelectItem key={status.value} value={status.value}>
                        <div className="flex items-center gap-2">
                          <div className={`h-2 w-2 rounded-full ${status.color}`} />
                          {status.label}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="resolution-notes">Resolution Notes</Label>
                <Textarea 
                  id="resolution-notes"
                  placeholder="Add notes about the resolution, steps taken, or communication with customer..."
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  className="min-h-[120px]"
                />
                <p className="text-xs text-muted-foreground">
                  These notes will be visible to customer support team
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedComplaint(null)}>
                Cancel
              </Button>
              <Button onClick={handleStatusUpdate} disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Update Complaint
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* View Details Dialog */}
      {selectedComplaint && (
        <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
          <DialogContent className="sm:max-w-[650px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Complaint Details</DialogTitle>
              <DialogDescription>
                ID: <span className="font-mono text-xs">{selectedComplaint.id}</span>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6">
              {/* Basic Information */}
              <div>
                <h3 className="text-sm font-semibold mb-2">Basic Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">Subject</Label>
                    <p className="font-medium">{selectedComplaint.subject}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Category</Label>
                    <div className="mt-1">{getCategoryBadge(selectedComplaint.category)}</div>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Priority</Label>
                    <div className="mt-1">{getPriorityBadge(selectedComplaint.priority)}</div>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Status</Label>
                    <div className="mt-1">{getStatusBadge(selectedComplaint.status)}</div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Customer Details */}
              <div>
                <h3 className="text-sm font-semibold mb-2">Customer Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">Name</Label>
                    <p>{selectedComplaint.customer_name || "Not provided"}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Email</Label>
                    <p>{selectedComplaint.customer_email || "Not provided"}</p>
                  </div>
                  {selectedComplaint.customer_phone && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Phone</Label>
                      <p>{selectedComplaint.customer_phone}</p>
                    </div>
                  )}
                  <div>
                    <Label className="text-xs text-muted-foreground">Created At</Label>
                    <p>{formatDate(selectedComplaint.created_at)}</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Order Details */}
              {selectedComplaint.order_id && (
                <>
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Order Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs text-muted-foreground">Order ID</Label>
                        <p className="font-mono text-sm">{selectedComplaint.order_id}</p>
                      </div>
                      {selectedComplaint.order_total && (
                        <div>
                          <Label className="text-xs text-muted-foreground">Order Total</Label>
                          <p>${parseFloat(selectedComplaint.order_total).toFixed(2)}</p>
                        </div>
                      )}
                      {selectedComplaint.product_name && (
                        <div className="col-span-2">
                          <Label className="text-xs text-muted-foreground">Product</Label>
                          <p>{selectedComplaint.product_name}</p>
                        </div>
                      )}
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Complaint Description */}
              <div>
                <h3 className="text-sm font-semibold mb-2">Description</h3>
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4">
                  <p className="whitespace-pre-line">{selectedComplaint.description || "No description provided"}</p>
                </div>
              </div>

              {/* Attachments */}
              {selectedComplaint.attachments && selectedComplaint.attachments.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Attachments</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedComplaint.attachments.map((attachment, index) => (
                        <Button key={index} variant="outline" size="sm">
                          View Attachment {index + 1}
                        </Button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Resolution Notes */}
              {selectedComplaint.resolution_notes && (
                <>
                  <Separator />
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Resolution Notes</h3>
                    <div className="bg-green-50 dark:bg-green-900/20 rounded-md p-4">
                      <p className="whitespace-pre-line">{selectedComplaint.resolution_notes}</p>
                      {selectedComplaint.resolved_at && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Resolved on: {formatDate(selectedComplaint.resolved_at)}
                        </p>
                      )}
                    </div>
                  </div>
                </>
              )}

              {/* Internal Notes */}
              {selectedComplaint.internal_notes && (
                <>
                  <Separator />
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Internal Notes</h3>
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-md p-4">
                      <p className="whitespace-pre-line">{selectedComplaint.internal_notes}</p>
                    </div>
                  </div>
                </>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
                Close
              </Button>
              <Button onClick={() => {
                setViewDialogOpen(false);
                openUpdateDialog(selectedComplaint);
              }}>
                Update Status
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}