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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter,
  DialogDescription
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  Monitor, 
  Store, 
  Plus, 
  Loader2, 
  RefreshCw, 
  MapPin,
  QrCode,
  Copy
} from 'lucide-react';
import { toast } from "sonner";

export default function Kiosks() {
  const [kiosks, setKiosks] = useState([]);
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    store_id: ""
  });

  // --- Fetch Data ---
  const fetchData = async () => {
    setLoading(true);
    try {
      const [kiosksData, storesData] = await Promise.all([
        AdminService.listKiosks(),
        AdminService.listStores()
      ]);
      
      setKiosks(Array.isArray(kiosksData) ? kiosksData : []);
      setStores(Array.isArray(storesData) ? storesData : storesData.data || []);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("Failed to load kiosks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // --- Create Kiosk ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.store_id) {
      toast.error("Please select a store");
      return;
    }

    setIsSubmitting(true);
    try {
      await AdminService.createKiosk(formData);
      toast.success("Kiosk created successfully");
      setIsDialogOpen(false);
      setFormData({ name: "", store_id: "" });
      fetchData(); // Refresh list
    } catch (error) {
      console.error("Create failed:", error);
      toast.error("Failed to create kiosk");
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("ID copied to clipboard");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Kiosk Devices</h1>
          <p className="text-muted-foreground">Manage physical terminals and associate them with stores</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </Button>
          <Button onClick={() => setIsDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Add Kiosk
          </Button>
        </div>
      </div>

      {/* List */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle>Registered Devices</CardTitle>
          <CardDescription>{kiosks.length} active terminals</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Kiosk Name</TableHead>
                  <TableHead>Assigned Store</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Device ID</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell colSpan={5} className="h-24 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto"/></TableCell></TableRow>
                ) : kiosks.length === 0 ? (
                  <TableRow><TableCell colSpan={5} className="h-24 text-center text-muted-foreground">No kiosks found. Add one to get started.</TableCell></TableRow>
                ) : (
                  kiosks.map((kiosk) => {
                    // Find store details for display
                    const store = stores.find(s => s.id === kiosk.store_id);
                    return (
                      <TableRow key={kiosk.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-full bg-slate-100">
                              <Monitor className="h-4 w-4 text-slate-600" />
                            </div>
                            <span className="font-medium">{kiosk.name}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Store className="h-3 w-3 text-muted-foreground" />
                            {store ? store.name : <span className="text-red-500">Unknown Store</span>}
                          </div>
                        </TableCell>
                        <TableCell>
                          {store && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <MapPin className="h-3 w-3" />
                              {store.city}, {store.state}
                            </div>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <code className="bg-muted px-2 py-1 rounded text-xs font-mono">{kiosk.id}</code>
                            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => copyToClipboard(kiosk.id)}>
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="outline" size="sm" onClick={() => window.open(`/kiosk/login?kiosk_id=${kiosk.id}`, '_blank')}>
                            <QrCode className="h-3 w-3 mr-2" /> Launch
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register New Kiosk</DialogTitle>
            <DialogDescription>Create a new terminal ID for a specific store location.</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Kiosk Name</Label>
                <Input 
                  id="name" 
                  placeholder="e.g. Entrance Terminal 01" 
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                />
              </div>
              
              <div className="grid gap-2">
                <Label>Select Store</Label>
                <Select 
                  value={formData.store_id} 
                  onValueChange={(val) => setFormData({...formData, store_id: val})}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a store..." />
                  </SelectTrigger>
                  <SelectContent>
                    {stores.map(store => (
                      <SelectItem key={store.id} value={store.id}>
                        {store.name} ({store.city})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Kiosk
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}