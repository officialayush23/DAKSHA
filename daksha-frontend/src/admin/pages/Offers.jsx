import React, { useEffect, useState } from 'react';
import { AdminService } from '@/lib/adminApi';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
  DialogTrigger, 
  DialogFooter 
} from "@/components/ui/dialog";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { 
  Plus, 
  Trash2, 
  Calendar, 
  Loader2, 
  Tag, 
  Edit2,
  Copy,
  Search,
  RefreshCw,
  Percent,
  DollarSign
} from 'lucide-react';
import { format } from 'date-fns';
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

export default function Offers() {
  const [offers, setOffers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingOffer, setEditingOffer] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Exact match with your backend schemas
  const initialFormState = {
    code: "",
    description: "",
    coupon_type: "percentage",
    value: 0,
    scope: "global",
    scope_value: "",
    min_order_value: 0,
    max_discount: 0,
    valid_to: "",
    status: "active" // active, expired, disabled
  };
  
  const [formData, setFormData] = useState(initialFormState);

  const fetchOffers = async () => {
    try {
      setLoading(true);
      const res = await AdminService.listOffers();
      setOffers(Array.isArray(res) ? res : []);
      toast.success("Coupons loaded successfully");
    } catch (error) {
      console.error("Failed to load offers:", error);
      toast.error("Failed to load coupons");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOffers();
  }, []);

const prepareFormData = (data) => {
    return {
      code: data.code.trim().toUpperCase(),
      description: data.description?.trim() || null,
      coupon_type: data.coupon_type,
      value: parseFloat(data.value) || 0,
      // Change how scope is handled to ensure exact string matching
      scope: data.scope === 'global' ? 'global_' : data.scope, // ✅ Maps to Python Enum Key
      scope_value: data.scope_value?.trim() || null,
      min_order_value: parseFloat(data.min_order_value) || null,
      max_discount: parseFloat(data.max_discount) || null,
      valid_to: data.valid_to ? new Date(data.valid_to).toISOString() : null,
      // Status mapping isn't strictly in CouponCreate, but good for local state if added later
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const payload = prepareFormData(formData);
      
      if (editingOffer) {
        await AdminService.updateOffer(editingOffer.id, payload);
        toast.success("Coupon updated successfully");
      } else {
        await AdminService.createOffer(payload);
        toast.success("Coupon created successfully");
      }
      
      setFormData(initialFormState);
      setEditingOffer(null);
      setIsDialogOpen(false);
      fetchOffers();
    } catch (error) {
      console.error("Failed to save offer:", error);
      toast.error(`Failed to save coupon: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this coupon?")) return;
    try {
      await AdminService.deleteOffer(id);
      setOffers(offers.filter(o => o.id !== id));
      toast.success("Coupon deleted successfully");
    } catch (error) {
      console.error("Failed to delete offer:", error);
      toast.error("Failed to delete coupon (Check if backend DELETE route exists)");
    }
  };

  const handleEdit = (offer) => {
    setEditingOffer(offer);
    const formattedData = {
      ...initialFormState,
      ...offer,
      valid_to: offer.valid_to ? format(new Date(offer.valid_to), "yyyy-MM-dd'T'HH:mm") : "",
    };
    setFormData(formattedData);
    setIsDialogOpen(true);
  };

  const handleDuplicate = (offer) => {
    setEditingOffer(null);
    setFormData({
      ...initialFormState,
      ...offer,
      code: `${offer.code}_COPY`,
      id: undefined
    });
    setIsDialogOpen(true);
  };

  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const filteredOffers = offers.filter(offer => {
    const matchesSearch = 
      offer.code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      offer.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === "all" || offer.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const stats = {
    total: offers.length,
    active: offers.filter(o => o.status === 'active').length,
    percentage: offers.filter(o => o.coupon_type === 'percentage').length,
    fixed: offers.filter(o => o.coupon_type === 'flat').length,
  };

  const formatCurrency = (amount) => {
    if (!amount) return "₹0";
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Coupons & Offers</h1>
          <p className="text-muted-foreground">Manage global and targeted discount codes</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={(open) => {
          if (!open) {
            setFormData(initialFormState);
            setEditingOffer(null);
          }
          setIsDialogOpen(open);
        }}>
          <DialogTrigger asChild>
            <Button><Plus className="mr-2 h-4 w-4" /> Create Coupon</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingOffer ? 'Edit Coupon' : 'Create New Coupon'}</DialogTitle>
              <DialogDescription>Configure discount rules and limitations.</DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4 py-4">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Basic Information</h3>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="code">Coupon Code *</Label>
                    <Input 
                      id="code"
                      placeholder="e.g. SUMMER24" 
                      value={formData.code} 
                      onChange={(e) => handleChange("code", e.target.value.toUpperCase())} 
                      required 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea 
                      id="description"
                      placeholder="Describe this coupon..." 
                      value={formData.description} 
                      onChange={(e) => handleChange("description", e.target.value)} 
                      rows={2}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Discount Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Discount Type *</Label>
                    <Select 
                      value={formData.coupon_type} 
                      onValueChange={(val) => handleChange("coupon_type", val)}
                    >
                      <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">
                          <div className="flex items-center gap-2"><Percent className="h-3 w-3" /> Percentage (%)</div>
                        </SelectItem>
                        <SelectItem value="flat">
                          <div className="flex items-center gap-2"><DollarSign className="h-3 w-3" /> Flat Amount (₹)</div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="value">Discount Value *</Label>
                    <Input 
                      id="value"
                      type="number" step="0.01" min="0"
                      placeholder={formData.coupon_type === 'percentage' ? 'e.g. 20' : 'e.g. 500'} 
                      value={formData.value} 
                      onChange={(e) => handleChange("value", e.target.value)} 
                      required 
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Scope</Label>
                    <Select value={formData.scope} onValueChange={(val) => handleChange("scope", val)}>
                      <SelectTrigger><SelectValue placeholder="Select scope" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="global">Global (All Products)</SelectItem>
                        <SelectItem value="category">Specific Category</SelectItem>
                        <SelectItem value="product">Specific Product</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="scope_value">Scope Target (Category Name / Product ID)</Label>
                    <Input 
                      id="scope_value"
                      placeholder="e.g. Shoes" 
                      value={formData.scope_value} 
                      onChange={(e) => handleChange("scope_value", e.target.value)} 
                      disabled={formData.scope === 'global'}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="min_order_value">Min Order Value (₹)</Label>
                    <Input 
                      id="min_order_value" type="number" step="0.01" min="0"
                      value={formData.min_order_value} 
                      onChange={(e) => handleChange("min_order_value", e.target.value)} 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="max_discount">Max Discount Cap (₹)</Label>
                    <Input 
                      id="max_discount" type="number" step="0.01" min="0"
                      value={formData.max_discount} 
                      onChange={(e) => handleChange("max_discount", e.target.value)} 
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Validity & Status</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="valid_to">Expiration Date</Label>
                    <Input 
                      id="valid_to" type="datetime-local" 
                      value={formData.valid_to} 
                      onChange={(e) => handleChange("valid_to", e.target.value)} 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Status</Label>
                    <Select value={formData.status} onValueChange={(val) => handleChange("status", val)}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="disabled">Disabled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <DialogFooter className="pt-4">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {editingOffer ? 'Update' : 'Create'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Total</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{stats.total}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-green-600">{stats.active}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">% Discounts</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-blue-600">{stats.percentage}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Flat Amount</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-purple-600">{stats.fixed}</div></CardContent></Card>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Discount</TableHead>
              <TableHead>Scope</TableHead>
              <TableHead>Expires</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={6} className="h-24 text-center"><Loader2 className="h-6 w-6 animate-spin mx-auto" /></TableCell></TableRow>
            ) : filteredOffers.length === 0 ? (
              <TableRow><TableCell colSpan={6} className="h-24 text-center text-muted-foreground">No coupons found.</TableCell></TableRow>
            ) : (
              filteredOffers.map((offer) => (
                <TableRow key={offer.id}>
                  <TableCell>
                    <div className="font-mono font-bold">{offer.code}</div>
                    <div className="text-xs text-muted-foreground">{offer.description}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {offer.coupon_type === 'percentage' ? `${offer.value}% OFF` : `${formatCurrency(offer.value)} OFF`}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">{offer.scope}</Badge>
                    {offer.scope_value && <div className="text-xs mt-1">{offer.scope_value}</div>}
                  </TableCell>
                  <TableCell>
                    {offer.valid_to ? format(new Date(offer.valid_to), 'MMM dd, yyyy') : 'No Expiry'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={offer.status === 'active' ? "default" : "destructive"}>
                      {offer.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(offer)}><Edit2 className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDuplicate(offer)}><Copy className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => handleDelete(offer.id)}><Trash2 className="h-4 w-4" /></Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}