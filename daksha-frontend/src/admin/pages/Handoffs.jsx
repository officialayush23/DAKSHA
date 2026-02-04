import React, { useEffect, useState } from 'react';
import { AdminService, apiClient } from '@/lib/adminApi';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  ArrowRightLeft, 
  MessageSquare,
  Truck, 
  Package, 
  Store, 
  User, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw, 
  Search, 
  Eye, 
  Send,
  MessageCircle,
  Archive,
  Phone,
  Mail,
  MapPin,
  Loader2
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

export default function Handoffs() {
  const [activeTab, setActiveTab] = useState("logistics");
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Data States
  const [logisticsData, setLogisticsData] = useState([]);
  const [chatData, setChatData] = useState([]);
  
  // Dialog States
  const [selectedItem, setSelectedItem] = useState(null);
  const [isLogisticsDialogOpen, setIsLogisticsDialogOpen] = useState(false);
  const [isChatDialogOpen, setIsChatDialogOpen] = useState(false);
  
  // Chat Reply State
  const [replyText, setReplyText] = useState('');
  const [sendingReply, setSendingReply] = useState(false);

  // --- FETCH DATA ---
  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === "logistics") {
        await fetchLogistics();
      } else {
        await fetchChats();
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  // 1. Fetch Logistics (Physical Handoffs)
  const fetchLogistics = async () => {
    try {
      // Priority 1: Try the direct Handoffs endpoint
      try {
        const data = await AdminService.getHandoffs();
        if (Array.isArray(data) && data.length > 0) {
          setLogisticsData(data);
          return;
        }
      } catch (e) {
        console.warn("Direct handoffs endpoint failed, switching to store aggregation.");
      }

      // Priority 2: Aggregate from Stores (Fallback)
      const stores = await AdminService.listStores();
      if (!Array.isArray(stores)) {
        setLogisticsData([]);
        return;
      }

      const allPickups = [];
      // Limit to first 5 stores to prevent overwhelming API calls in this demo
      for (const store of stores.slice(0, 5)) {
        try {
          const pickups = await AdminService.listStorePickups(store.id);
          if (Array.isArray(pickups)) {
            allPickups.push(...pickups.map(p => ({
              ...p,
              type: 'pickup', // Tag as pickup
              store_name: store.name,
              store_city: store.city
            })));
          }
        } catch (err) {
          console.error(`Error fetching pickups for store ${store.id}`);
        }
      }
      setLogisticsData(allPickups);

    } catch (error) {
      console.error("Logistics fetch error:", error);
      toast.error("Failed to load logistics data");
    }
  };

  // 2. Fetch Support (Chat Handoffs)
  const fetchChats = async () => {
    try {
      const data = await AdminService.getChatHandoffs();
      setChatData(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Chat fetch error:", error);
      toast.error("Failed to load chat sessions");
    }
  };

  // 3. Send Admin Reply
  const handleSendReply = async () => {
    if (!replyText.trim() || !selectedItem) return;
    
    setSendingReply(true);
    try {
      // Calls POST /admin/chat/message/{session_id}?message=...
      // Note: passing message as query param based on your curl definition
      await apiClient(
        `/admin/chat/message/${selectedItem.id}`, 
        'POST', 
        null, 
        { message: replyText } 
      );
      
      toast.success("Reply sent successfully");
      setReplyText("");
      setIsChatDialogOpen(false);
      fetchChats(); // Refresh list
    } catch (error) {
      console.error("Reply error:", error);
      toast.error("Failed to send message");
    } finally {
      setSendingReply(false);
    }
  };

  // --- HELPERS ---
  const getStatusBadge = (status) => {
    const s = status?.toLowerCase();
    if (s === 'completed' || s === 'resolved') return <Badge className="bg-green-600"><CheckCircle className="w-3 h-3 mr-1"/>{status}</Badge>;
    if (s === 'pending' || s === 'created') return <Badge className="bg-yellow-100 text-yellow-800"><Clock className="w-3 h-3 mr-1"/>{status}</Badge>;
    if (s === 'active') return <Badge className="bg-blue-600"><MessageCircle className="w-3 h-3 mr-1"/>Active</Badge>;
    if (s === 'cancelled' || s === 'failed') return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1"/>{status}</Badge>;
    return <Badge variant="outline">{status}</Badge>;
  };

  // Filter Logic
  const filterData = (data) => {
    if (!searchTerm) return data;
    const lowerTerm = searchTerm.toLowerCase();
    return data.filter(item => 
      item.id?.toLowerCase().includes(lowerTerm) ||
      item.store_name?.toLowerCase().includes(lowerTerm) ||
      item.user_name?.toLowerCase().includes(lowerTerm) ||
      item.user_email?.toLowerCase().includes(lowerTerm)
    );
  };

  const filteredLogistics = filterData(logisticsData);
  const filteredChats = filterData(chatData);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Operations & Handoffs</h1>
          <p className="text-muted-foreground">Manage physical transfers and customer support escalations</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="logistics" className="flex gap-2">
            <Truck className="h-4 w-4" /> Logistics (Pickups)
          </TabsTrigger>
          <TabsTrigger value="chat" className="flex gap-2">
            <MessageSquare className="h-4 w-4" /> Support (Chats)
          </TabsTrigger>
        </TabsList>

        {/* --- TAB 1: LOGISTICS --- */}
        <TabsContent value="logistics" className="space-y-4">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search pickups, stores, orders..." 
                className="pl-9"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Physical Handoffs</CardTitle>
              <CardDescription>Store pickups and inventory transfers</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={6} className="h-24 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto"/></TableCell></TableRow>
                  ) : filteredLogistics.length === 0 ? (
                    <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">No handoffs found</TableCell></TableRow>
                  ) : (
                    filteredLogistics.map(item => (
                      <TableRow key={item.id}>
                        <TableCell className="font-mono text-xs">{item.id.slice(0,8)}...</TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">{item.store_name || 'Unknown Store'}</span>
                            <span className="text-xs text-muted-foreground">{item.store_city}</span>
                          </div>
                        </TableCell>
                        <TableCell><Badge variant="secondary">Pickup</Badge></TableCell>
                        <TableCell>{getStatusBadge(item.status)}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {item.created_at ? format(new Date(item.created_at), 'MMM dd') : 'N/A'}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" onClick={() => { setSelectedItem(item); setIsLogisticsDialogOpen(true); }}>
                            <Eye className="h-4 w-4"/>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* --- TAB 2: CHATS --- */}
        <TabsContent value="chat" className="space-y-4">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input 
                placeholder="Search user email, name..." 
                className="pl-9"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle>Active Chat Sessions</CardTitle>
              <CardDescription>Customer support escalations requiring attention</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Session ID</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Last Message</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Started</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow><TableCell colSpan={6} className="h-24 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto"/></TableCell></TableRow>
                  ) : filteredChats.length === 0 ? (
                    <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">No active chat sessions</TableCell></TableRow>
                  ) : (
                    filteredChats.map(chat => (
                      <TableRow key={chat.id}>
                        <TableCell className="font-mono text-xs">{chat.id.slice(0,8)}...</TableCell>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">{chat.user_name || 'Guest'}</span>
                            <span className="text-xs text-muted-foreground">{chat.user_email}</span>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-[200px] truncate text-muted-foreground">
                          {chat.last_message || "No messages yet"}
                        </TableCell>
                        <TableCell>{getStatusBadge(chat.status)}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {chat.created_at ? formatDistanceToNow(new Date(chat.created_at), { addSuffix: true }) : 'N/A'}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" onClick={() => { setSelectedItem(chat); setIsChatDialogOpen(true); }}>
                            Reply
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* --- DIALOG 1: LOGISTICS DETAILS --- */}
      <Dialog open={isLogisticsDialogOpen} onOpenChange={setIsLogisticsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Pickup Details</DialogTitle>
            <DialogDescription>ID: <span className="font-mono">{selectedItem?.id}</span></DialogDescription>
          </DialogHeader>
          {selectedItem && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><Label className="text-muted-foreground text-xs">Store</Label><p className="font-medium">{selectedItem.store_name}</p></div>
                <div><Label className="text-muted-foreground text-xs">Customer</Label><p className="font-medium">{selectedItem.customer_name || 'N/A'}</p></div>
                <div><Label className="text-muted-foreground text-xs">Status</Label><div className="mt-1">{getStatusBadge(selectedItem.status)}</div></div>
                <div><Label className="text-muted-foreground text-xs">Items</Label><p className="font-medium">{selectedItem.items_count || 1}</p></div>
              </div>
              <div><Label className="text-muted-foreground text-xs">Order ID</Label><p className="font-mono text-sm">{selectedItem.order_id || 'N/A'}</p></div>
            </div>
          )}
          <DialogFooter><Button variant="outline" onClick={() => setIsLogisticsDialogOpen(false)}>Close</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      {/* --- DIALOG 2: CHAT REPLY --- */}
      <Dialog open={isChatDialogOpen} onOpenChange={setIsChatDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Reply to User</DialogTitle>
            <DialogDescription>
              Session: <span className="font-mono text-primary">{selectedItem?.id}</span>
            </DialogDescription>
          </DialogHeader>
          
          {selectedItem && (
            <div className="space-y-4 py-2">
              <div className="bg-muted/50 p-3 rounded-md">
                <Label className="text-xs text-muted-foreground mb-1 block">User Info</Label>
                <div className="flex items-center gap-2 mb-1"><User className="h-3 w-3"/> <span className="text-sm font-medium">{selectedItem.user_name}</span></div>
                <div className="flex items-center gap-2"><Mail className="h-3 w-3"/> <span className="text-sm">{selectedItem.user_email}</span></div>
              </div>

              <div className="space-y-2">
                <Label>Your Message</Label>
                <Textarea 
                  placeholder="Type your response here..." 
                  rows={4}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsChatDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSendReply} disabled={sendingReply}>
              {sendingReply && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Send Message
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}