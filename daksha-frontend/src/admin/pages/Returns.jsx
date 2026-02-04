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
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription 
} from "@/components/ui/card";
import { 
  Loader2, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Undo2,
  AlertCircle
} from 'lucide-react';
import { toast } from "sonner";

export default function Returns() {
  const [returns, setReturns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  // 1. Fetch Returns
  const fetchReturns = async () => {
    try {
      setLoading(true);
      const data = await AdminService.listReturns();
      setReturns(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to fetch returns:", error);
      toast.error("Failed to load returns");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturns();
  }, []);

  // 2. Handle Status Update (Approve/Reject)
  const handleUpdateStatus = async (id, newStatus) => {
    try {
      setProcessingId(id);
      // Calls PATCH /admin/returns/{id}?status=...
      await AdminService.updateReturn(id, newStatus);
      
      toast.success(`Return request ${newStatus}`);
      fetchReturns(); // Refresh list
    } catch (error) {
      console.error("Update failed:", error);
      toast.error("Failed to update return status");
    } finally {
      setProcessingId(null);
    }
  };

  // Helper for Status Badge
  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'approved':
      case 'completed':
        return <Badge className="bg-green-600"><CheckCircle className="w-3 h-3 mr-1"/> Approved</Badge>;
      case 'rejected':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1"/> Rejected</Badge>;
      case 'pending':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200">Pending</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Returns Management</h1>
          <p className="text-muted-foreground">Process customer return requests and refunds</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchReturns} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Return Requests</CardTitle>
          <CardDescription>Manage incoming return requests from customers</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Return ID</TableHead>
                  <TableHead>Order ID</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center">
                      <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
                    </TableCell>
                  </TableRow>
                ) : returns.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-32 text-center text-muted-foreground">
                      <div className="flex flex-col items-center justify-center">
                        <Undo2 className="h-8 w-8 mb-2 opacity-50" />
                        <p>No active return requests found</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  returns.map((ret) => (
                    <TableRow key={ret.id}>
                      <TableCell className="font-mono text-xs">{ret.id.slice(0, 8)}...</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {ret.order_id ? ret.order_id.slice(0, 8) + '...' : 'N/A'}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate" title={ret.reason}>
                        {ret.reason || "No reason provided"}
                      </TableCell>
                      <TableCell>{getStatusBadge(ret.status)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {ret.created_at ? new Date(ret.created_at).toLocaleDateString() : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right">
                        {ret.status === 'pending' && (
                          <div className="flex justify-end gap-2">
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="text-green-600 hover:text-green-700 hover:bg-green-50"
                              onClick={() => handleUpdateStatus(ret.id, 'approved')}
                              disabled={!!processingId}
                            >
                              {processingId === ret.id ? <Loader2 className="w-4 h-4 animate-spin"/> : "Approve"}
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              onClick={() => handleUpdateStatus(ret.id, 'rejected')}
                              disabled={!!processingId}
                            >
                              {processingId === ret.id ? <Loader2 className="w-4 h-4 animate-spin"/> : "Reject"}
                            </Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}