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
  MessageSquare,
  Users, 
  Clock, 
  Loader2, 
  RefreshCw, 
  Search,
  Eye,
  CheckCircle,
  XCircle,
  AlertCircle,
  Phone,
  Mail,
  User,
  Calendar,
  MapPin,
  PhoneCall,
  MessageCircle,
  Archive,
  Send,
  Clock as ClockIcon,
  Filter,
  Info
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

export default function AdminHandoff() {
  const [handoffs, setHandoffs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedHandoff, setSelectedHandoff] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [replying, setReplying] = useState(false);

  // Status options for chat handoffs
  const STATUS_OPTIONS = ['all', 'pending', 'active', 'resolved', 'closed'];

  // --- Fetch Data ---
  const fetchHandoffs = async () => {
    try {
      setLoading(true);
      
      // Use the new chat handoffs endpoint
      const handoffsData = await AdminService.getChatHandoffs();
      
      if (Array.isArray(handoffsData)) {
        setHandoffs(handoffsData);
        toast.success(`Loaded ${handoffsData.length} chat handoffs`);
      } else {
        setHandoffs([]);
      }
      
    } catch (error) {
      console.error("Failed to fetch chat handoffs:", error);
      toast.error("Failed to load chat handoffs");
      setHandoffs([]);
    } finally {
      setLoading(false);
    }
  };

  // Since we only have GET endpoint for now, we'll disable update functions
  const updateHandoffStatus = async (handoffId, status, resolutionNotes = '') => {
    try {
      // Note: This endpoint may not exist yet in the API
      // For now, just show a message
      toast.info("Update functionality not available yet");
      return;
    } catch (error) {
      console.error('Error updating handoff:', error);
      toast.error('Failed to update handoff');
      throw error;
    }
  };

  const sendReply = async (handoffId) => {
    if (!replyText.trim()) {
      toast.error('Please enter a reply message');
      return;
    }
    
    try {
      setReplying(true);
      // Note: This endpoint may not exist yet in the API
      toast.info("Reply functionality not available yet");
      setReplyText('');
      
    } catch (error) {
      console.error('Error sending reply:', error);
      toast.error('Failed to send reply');
    } finally {
      setReplying(false);
    }
  };

  useEffect(() => {
    fetchHandoffs();
  }, []);

  // Helper for Status Badge
  const getStatusBadge = (status) => {
    switch(status?.toLowerCase()) {
      case 'active': 
        return (
          <Badge className="bg-blue-600 hover:bg-blue-700">
            <MessageCircle className="w-3 h-3 mr-1" />
            Active
          </Badge>
        );
      case 'pending': 
        return (
          <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200">
            <ClockIcon className="w-3 h-3 mr-1" />
            Pending
          </Badge>
        );
      case 'resolved': 
        return (
          <Badge className="bg-green-600 hover:bg-green-700">
            <CheckCircle className="w-3 h-3 mr-1" />
            Resolved
          </Badge>
        );
      case 'closed': 
        return (
          <Badge className="bg-gray-600 hover:bg-gray-700">
            <Archive className="w-3 h-3 mr-1" />
            Closed
          </Badge>
        );
      default: 
        return <Badge variant="outline">{status || 'Unknown'}</Badge>;
    }
  };

  // Filter handoffs
  const filteredHandoffs = handoffs.filter(handoff => {
    const matchesSearch = 
      handoff.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      handoff.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      handoff.user_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (handoff.subject && handoff.subject.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (handoff.last_message && handoff.last_message.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesStatus = filterStatus === 'all' || handoff.status === filterStatus;
    
    return matchesSearch && matchesStatus;
  });

  // Calculate statistics
  const calculateStats = () => {
    const stats = {
      total: handoffs.length,
      active: handoffs.filter(h => h.status === 'active').length,
      pending: handoffs.filter(h => h.status === 'pending').length,
      resolved: handoffs.filter(h => h.status === 'resolved').length,
      closed: handoffs.filter(h => h.status === 'closed').length,
      today: handoffs.filter(h => {
        if (!h.created_at) return false;
        const handoffDate = new Date(h.created_at);
        const today = new Date();
        return handoffDate.toDateString() === today.toDateString();
      }).length
    };
    
    return stats;
  };

  const stats = calculateStats();

  // View handoff details
  const viewHandoffDetails = (handoff) => {
    setSelectedHandoff(handoff);
    setViewDialogOpen(true);
  };

  // Action handlers (disabled for now)
  const handleResolve = async () => {
    if (!selectedHandoff) return;
    
    try {
      await updateHandoffStatus(selectedHandoff.id, 'resolved', 'Resolved by admin');
      setViewDialogOpen(false);
    } catch (error) {
      console.error('Failed to resolve:', error);
    }
  };

  const handleClose = async () => {
    if (!selectedHandoff) return;
    
    try {
      await updateHandoffStatus(selectedHandoff.id, 'closed', 'Closed by admin');
      setViewDialogOpen(false);
    } catch (error) {
      console.error('Failed to close:', error);
    }
  };

  const handleReopen = async () => {
    if (!selectedHandoff) return;
    
    try {
      await updateHandoffStatus(selectedHandoff.id, 'active', 'Re-opened by admin');
      setViewDialogOpen(false);
    } catch (error) {
      console.error('Failed to reopen:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Chat Handoffs</h1>
          <p className="text-muted-foreground">Manage customer support conversations and escalations</p>
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
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-xs text-muted-foreground">
              {stats.today} today
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <MessageCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.active}</div>
            <div className="text-xs text-muted-foreground">
              {stats.pending} pending
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
            <div className="text-xs text-muted-foreground">
              {stats.total > 0 ? Math.round((stats.resolved / stats.total) * 100) : 0}% rate
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Closed</CardTitle>
            <Archive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats.closed}</div>
            <div className="text-xs text-muted-foreground">
              Completed conversations
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
              placeholder="Search by ID, user, or email..."
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
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Handoff Table */}
      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center">
                  <div className="flex justify-center items-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin" /> 
                    Loading chat handoffs...
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredHandoffs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <MessageSquare className="h-8 w-8 mb-2 opacity-50" />
                    <p>No chat handoffs found</p>
                    <p className="text-sm">
                      {handoffs.length === 0 
                        ? "No chat handoffs in the system" 
                        : "Try adjusting your search or filters"}
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredHandoffs.map((handoff) => (
                <TableRow key={handoff.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <TableCell className="font-mono text-xs">
                    {handoff.id.slice(0, 8)}...
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        <span className="font-medium">{handoff.user_name || 'Unknown User'}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {handoff.user_email || 'No email'}
                      </div>
                    </div>
                  </TableCell>
                  
                  <TableCell>
                    <div className="space-y-1">
                      <div className="text-sm">
                        {handoff.created_at ? format(new Date(handoff.created_at), 'MMM dd') : "N/A"}
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
          <DialogContent className="sm:max-w-[700px]">
            <DialogHeader>
              <DialogTitle>Chat Handoff Details</DialogTitle>
              <DialogDescription>
                ID: <span className="font-mono text-xs">{selectedHandoff.id || 'N/A'}</span>
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              {/* User Info */}
              <div className="space-y-2">
                <Label className="text-sm font-semibold flex items-center gap-2">
                  <User className="h-4 w-4" /> User Information
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">User Name</Label>
                    <p className="font-medium">{selectedHandoff.user_name || 'Unknown User'}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">User Email</Label>
                    <p className="flex items-center gap-1">
                      <Mail className="h-3 w-3" />
                      {selectedHandoff.user_email || 'No email'}
                    </p>
                  </div>
                  {selectedHandoff.user_phone && (
                    <div>
                      <Label className="text-xs text-muted-foreground">Phone</Label>
                      <p className="flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {selectedHandoff.user_phone}
                      </p>
                    </div>
                  )}
                  {selectedHandoff.user_id && (
                    <div>
                      <Label className="text-xs text-muted-foreground">User ID</Label>
                      <p className="font-mono text-sm">{selectedHandoff.user_id}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Handoff Info */}
              <div className="space-y-2">
                <Label className="text-sm font-semibold flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" /> Handoff Information
                </Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">Status</Label>
                    <div className="mt-1">{getStatusBadge(selectedHandoff.status)}</div>
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Created</Label>
                    <p>{selectedHandoff.created_at ? format(new Date(selectedHandoff.created_at), 'PPP pp') : 'N/A'}</p>
                  </div>
                  {selectedHandoff.subject && (
                    <div className="col-span-2">
                      <Label className="text-xs text-muted-foreground">Subject</Label>
                      <p className="font-medium">{selectedHandoff.subject}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Timestamps */}
              <div className="space-y-2">
                <Label className="text-sm font-semibold flex items-center gap-2">
                  <Calendar className="h-4 w-4" /> Timestamps
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
                </div>
              </div>

              {/* Note about limited functionality */}
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <Info className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300">Limited Functionality</p>
                    <p className="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
                      Currently only the GET endpoint is available. Update and reply functionality will be available once the API endpoints are implemented.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <DialogFooter className="flex justify-between items-center">
              <div className="text-xs text-muted-foreground">
                Handoff ID: <span className="font-mono">{selectedHandoff.id}</span>
              </div>
              <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

    </div>
  );
}