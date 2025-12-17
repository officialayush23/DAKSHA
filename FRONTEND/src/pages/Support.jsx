// FRONTEND/src/pages/Support.jsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { supabase } from "@/lib/supabaseClient";
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
    order_id: "none"
  });

  // --- 1. Fetch Data ---
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        if (!user) return;

        // A. Fetch Tickets
        const { data: ticketData, error: ticketError } = await supabase
          .from('support_tickets')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });

        if (ticketError) throw ticketError;
        setTickets(ticketData || []);

        // B. Fetch Recent Orders (for the dropdown)
        const { data: orderData } = await supabase
          .from('orders')
          .select('id, total_amount, created_at, status')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })
          .limit(5);
        
        setRecentOrders(orderData || []);

      } catch (err) {
        console.error("Support load error:", err);
        toast.error("Failed to load support data.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user]);

  // --- 2. Create Ticket Handler ---
  const handleSubmit = async () => {
    if (!formData.issue_summary || !formData.details) {
      toast.error("Please provide a summary and details.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        user_id: user.id,
        issue_summary: formData.issue_summary,
        // We map 'details' to 'conversation_summary' as the initial message
        conversation_summary: formData.details, 
        priority: formData.priority,
        ticket_status: 'open',
        // Handle optional order_id
        order_id: formData.order_id === "none" ? null : formData.order_id,
        // Basic sentiment score init
        sentiment_score: 0.5 
      };

      const { data, error } = await supabase
        .from('support_tickets')
        .insert(payload)
        .select()
        .single();

      if (error) throw error;

      setTickets([data, ...tickets]);
      setIsCreateOpen(false);
      setFormData({ issue_summary: "", details: "", priority: "medium", order_id: "none" });
      toast.success("Ticket created successfully!");

    } catch (err) {
      console.error(err);
      toast.error("Failed to create ticket.");
    } finally {
      setSubmitting(false);
    }
  };

  // --- Helpers ---
  const getStatusBadge = (status) => {
    switch (status) {
      case 'open': return <Badge variant="default" className="bg-blue-600">Open</Badge>;
      case 'resolved': return <Badge variant="secondary" className="bg-emerald-100 text-emerald-700">Resolved</Badge>;
      case 'closed': return <Badge variant="outline">Closed</Badge>;
      default: return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return "text-red-600 bg-red-50 border-red-200";
      case 'high': return "text-orange-600 bg-orange-50 border-orange-200";
      case 'medium': return "text-blue-600 bg-blue-50 border-blue-200";
      default: return "text-slate-600 bg-slate-50 border-slate-200";
    }
  };

  if (loading) return <SupportSkeleton />;

  return (
    <div className="container max-w-5xl mx-auto py-6 px-4 space-y-6 min-h-screen">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Button variant="ghost" className="pl-0 gap-2 mb-1" onClick={() => navigate("/home")}>
            <ArrowLeft className="h-4 w-4" /> Home
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Support & Help</h1>
          <p className="text-muted-foreground">Track your tickets and get help with your orders.</p>
        </div>

        {/* Create Ticket Dialog */}
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 shadow-lg">
              <Plus className="h-4 w-4" /> Create New Ticket
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Submit a Support Ticket</DialogTitle>
              <DialogDescription>
                Describe your issue below. Our AI agent will review it immediately.
              </DialogDescription>
            </DialogHeader>
            
            <div className="grid gap-4 py-4">
              {/* Issue Summary */}
              <div className="space-y-2">
                <Label htmlFor="summary">Issue Summary</Label>
                <Input 
                  id="summary" 
                  placeholder="e.g. Wrong item received" 
                  value={formData.issue_summary}
                  onChange={(e) => setFormData({...formData, issue_summary: e.target.value})}
                />
              </div>

              {/* Related Order */}
              <div className="space-y-2">
                <Label>Related Order (Optional)</Label>
                <Select 
                  value={formData.order_id} 
                  onValueChange={(val) => setFormData({...formData, order_id: val})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an order" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No specific order</SelectItem>
                    {recentOrders.map(order => (
                      <SelectItem key={order.id} value={order.id}>
                        Order #{order.id.slice(0,8).toUpperCase()} - ₹{order.total_amount}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Priority */}
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select 
                  value={formData.priority} 
                  onValueChange={(val) => setFormData({...formData, priority: val})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low - General Question</SelectItem>
                    <SelectItem value="medium">Medium - Order Issue</SelectItem>
                    <SelectItem value="high">High - Payment/Refund</SelectItem>
                    <SelectItem value="urgent">Urgent - Security/Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Details */}
              <div className="space-y-2">
                <Label htmlFor="details">Details</Label>
                <Textarea 
                  id="details" 
                  className="min-h-[100px]"
                  placeholder="Please describe what happened..." 
                  value={formData.details}
                  onChange={(e) => setFormData({...formData, details: e.target.value})}
                />
              </div>
            </div>

            <DialogFooter>
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Send className="h-4 w-4 mr-2" />}
                Submit Ticket
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Ticket List */}
      <div className="grid gap-6">
        {tickets.length === 0 ? (
          <Card className="border-dashed py-12 flex flex-col items-center justify-center text-center">
            <div className="bg-muted/50 p-4 rounded-full mb-4">
              <LifeBuoy className="h-10 w-10 text-muted-foreground/50" />
            </div>
            <h3 className="text-lg font-semibold">No tickets yet</h3>
            <p className="text-muted-foreground max-w-sm mt-1">
              You haven't raised any support requests. Need help? Create a ticket above.
            </p>
          </Card>
        ) : (
          tickets.map((ticket) => (
            <Card key={ticket.id} className="group hover:border-primary/50 transition-all duration-300">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-muted-foreground">#{ticket.id.slice(0, 8)}</span>
                      <Badge variant="outline" className={`capitalize border ${getPriorityColor(ticket.priority)}`}>
                        {ticket.priority}
                      </Badge>
                    </div>
                    <CardTitle className="text-lg">{ticket.issue_summary}</CardTitle>
                  </div>
                  {getStatusBadge(ticket.ticket_status)}
                </div>
              </CardHeader>
              
              <CardContent className="pb-3">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {ticket.conversation_summary || "No details provided."}
                </p>
                {ticket.order_id && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 w-fit px-2 py-1 rounded">
                    <Package className="h-3 w-3" /> Related to Order #{ticket.order_id.slice(0,8)}
                  </div>
                )}
              </CardContent>
              
              <CardFooter className="pt-3 border-t bg-muted/5 flex justify-between items-center text-xs text-muted-foreground">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {format(new Date(ticket.created_at), "PP p")}
                  </span>
                  {ticket.resolved_by && (
                    <span className="flex items-center gap-1 text-emerald-600 font-medium">
                      <CheckCircle2 className="h-3 w-3" /> Resolved by {ticket.resolved_by}
                    </span>
                  )}
                </div>
                {/* Optional: Add 'View Details' button if you create a Ticket Detail page later */}
                {/* <Button variant="ghost" size="sm" className="h-6 text-xs">View Details</Button> */}
              </CardFooter>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

function Loader2({ className }) {
  return <svg className={`animate-spin ${className}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>;
}

function SupportSkeleton() {
  return (
    <div className="container max-w-5xl mx-auto py-6 px-4 space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-32" />
      </div>
      <div className="space-y-4">
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-40 w-full rounded-xl" />)}
      </div>
    </div>
  );
}