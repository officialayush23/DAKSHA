// FRONTEND/src/pages/Support.jsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { format } from "date-fns";
import { 
  LifeBuoy, MessageSquare, Plus, AlertCircle, CheckCircle2, 
  Clock, ArrowLeft, ChevronDown, Package, Send
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function SupportPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState([]);
  const [recentOrders, setRecentOrders] = useState([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // New Ticket Form State
  const [formData, setFormData] = useState({
    issue_summary: "",
    details: "",
    priority: "medium",
    order_id: "none",
    ticket_type: "general"
  });

  // --- 1. Fetch Data via API ---
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        if (!user) return;

        // A. Fetch Tickets via API
        const ticketsRes = await api.get("/support/tickets");
        setTickets(ticketsRes.data.tickets || []);

        // B. Fetch Recent Orders (for the dropdown) - using orders API
        const ordersRes = await api.get("/orders?limit=5");
        setRecentOrders(ordersRes.data.orders || []);

      } catch (err) {
        console.error("Support load error:", err);
        toast.error("Failed to load support data.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user]);

  // --- 2. Create Ticket Handler via API ---
  const handleSubmit = async () => {
    if (!formData.issue_summary || !formData.details) {
      toast.error("Please provide a summary and details.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        issue_summary: formData.issue_summary,
        conversation_summary: formData.details,
        priority: formData.priority,
        ticket_type: formData.ticket_type,
        order_id: formData.order_id === "none" ? null : formData.order_id,
        sentiment_score: 0.5
      };

      const res = await api.post("/support/tickets", payload);
      
      if (res.data.ticket) {
        setTickets([res.data.ticket, ...tickets]);
        setIsCreateOpen(false);
        setFormData({ issue_summary: "", details: "", priority: "medium", order_id: "none", ticket_type: "general" });
        toast.success("Ticket created successfully!");
      }

    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.detail || "Failed to create ticket.");
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      open: "default",
      investigating: "secondary",
      awaiting_user: "outline",
      resolved: "success",
      closed: "secondary"
    };
    return <Badge variant={variants[status] || "default"}>{status}</Badge>;
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      low: "bg-blue-100 text-blue-800",
      medium: "bg-yellow-100 text-yellow-800",
      high: "bg-orange-100 text-orange-800",
      urgent: "bg-red-100 text-red-800"
    };
    return <Badge className={colors[priority] || colors.medium}>{priority}</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto space-y-4">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <LifeBuoy className="h-8 w-8 text-primary" />
                Support Center
              </h1>
              <p className="text-muted-foreground">Manage your support tickets</p>
            </div>
          </div>
          
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New Ticket
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Support Ticket</DialogTitle>
                <DialogDescription>
                  Describe your issue and we'll help you resolve it.
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                <div>
                  <Label>Issue Type</Label>
                  <Select value={formData.ticket_type} onValueChange={(v) => setFormData({...formData, ticket_type: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="order_issue">Order Issue</SelectItem>
                      <SelectItem value="payment_issue">Payment Issue</SelectItem>
                      <SelectItem value="inventory_issue">Inventory Issue</SelectItem>
                      <SelectItem value="delivery_issue">Delivery Issue</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Summary *</Label>
                  <Input
                    placeholder="Brief description of the issue"
                    value={formData.issue_summary}
                    onChange={(e) => setFormData({...formData, issue_summary: e.target.value})}
                  />
                </div>

                <div>
                  <Label>Details *</Label>
                  <Textarea
                    placeholder="Provide more details about your issue..."
                    rows={5}
                    value={formData.details}
                    onChange={(e) => setFormData({...formData, details: e.target.value})}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Priority</Label>
                    <Select value={formData.priority} onValueChange={(v) => setFormData({...formData, priority: v})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label>Related Order (Optional)</Label>
                    <Select value={formData.order_id} onValueChange={(v) => setFormData({...formData, order_id: v})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        {recentOrders.map(order => (
                          <SelectItem key={order.id} value={order.id}>
                            Order #{order.id.slice(0, 8)} - {format(new Date(order.created_at), "MMM d, yyyy")}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                <Button onClick={handleSubmit} disabled={submitting}>
                  {submitting ? "Creating..." : "Create Ticket"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Tickets List */}
        {tickets.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <MessageSquare className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No tickets yet</h3>
              <p className="text-muted-foreground text-center mb-4">
                Create a new ticket to get help with your issue.
              </p>
              <Button onClick={() => setIsCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Ticket
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {tickets.map(ticket => (
              <Card key={ticket.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{ticket.subject || ticket.issue_summary}</CardTitle>
                      <CardDescription className="mt-1">
                        {format(new Date(ticket.created_at), "MMM d, yyyy 'at' h:mm a")}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      {getStatusBadge(ticket.status)}
                      {getPriorityBadge(ticket.priority)}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {ticket.description || ticket.conversation_summary || "No description provided."}
                  </p>
                  {ticket.order_id && (
                    <div className="mt-3 flex items-center gap-2 text-sm">
                      <Package className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Related to Order: {ticket.order_id.slice(0, 8)}</span>
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex justify-between">
                  <div className="text-xs text-muted-foreground">
                    Type: <span className="capitalize">{ticket.ticket_type}</span>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => navigate(`/support/${ticket.id}`)}>
                    View Details
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
