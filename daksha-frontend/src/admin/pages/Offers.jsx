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
  DollarSign,
  Check,
  X
} from 'lucide-react';
import { format } from 'date-fns';
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

  // Discount types from your API schema
  const DISCOUNT_TYPES = ['percentage', 'fixed'];
  
  // Form State matching your exact API Schema
  const initialFormState = {
    name: "",
    description: "",
    discount_type: "percentage",
    discount_value: 0,
    min_cart_value: 0,
    max_discount_amount: 0,
    eligible_category: "",
    stackable: true,
    valid_from: "",
    valid_to: "",
    active: true
  };
  
  const [formData, setFormData] = useState(initialFormState);

  // --- 1. Fetch Offers ---
  const fetchOffers = async () => {
    try {
      setLoading(true);
      const res = await AdminService.listOffers();
      setOffers(Array.isArray(res) ? res : []);
      toast.success("Offers loaded successfully");
    } catch (error) {
      console.error("Failed to load offers:", error);
      toast.error("Failed to load offers");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOffers();
  }, []);

  // --- 2. Prepare Form Data for API ---
  const prepareFormData = (data) => {
    const payload = {
      name: data.name.trim(),
      description: data.description?.trim() || "",
      discount_type: data.discount_type,
      discount_value: parseFloat(data.discount_value) || 0,
      min_cart_value: parseFloat(data.min_cart_value) || 0,
      max_discount_amount: parseFloat(data.max_discount_amount) || 0,
      eligible_category: data.eligible_category?.trim() || "",
      stackable: Boolean(data.stackable),
      valid_from: data.valid_from || null,
      valid_to: data.valid_to || null,
      active: Boolean(data.active)
    };
    
    return payload;
  };

  // --- 3. Handle Form Submit (Create/Update) ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const payload = prepareFormData(formData);
      console.log("Submitting offer data:", payload);
      
      if (editingOffer) {
        await AdminService.updateOffer(editingOffer.id, payload);
        toast.success("Offer updated successfully");
      } else {
        await AdminService.createOffer(payload);
        toast.success("Offer created successfully");
      }
      
      setFormData(initialFormState);
      setEditingOffer(null);
      setIsDialogOpen(false);
      fetchOffers();
    } catch (error) {
      console.error("Failed to save offer:", error);
      toast.error(`Failed to save offer: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- 4. Handle Delete ---
  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this offer?")) return;
    try {
      await AdminService.deleteOffer(id);
      setOffers(offers.filter(o => o.id !== id));
      toast.success("Offer deleted successfully");
    } catch (error) {
      console.error("Failed to delete offer:", error);
      toast.error("Failed to delete offer");
    }
  };

  // --- 5. Handle Edit ---
  const handleEdit = (offer) => {
    setEditingOffer(offer);
    const formattedData = {
      ...initialFormState,
      ...offer,
      // Format dates for datetime-local input
      valid_from: offer.valid_from ? format(new Date(offer.valid_from), "yyyy-MM-dd'T'HH:mm") : "",
      valid_to: offer.valid_to ? format(new Date(offer.valid_to), "yyyy-MM-dd'T'HH:mm") : "",
    };
    setFormData(formattedData);
    setIsDialogOpen(true);
  };

  // --- 6. Handle Status Toggle ---
  const handleToggleStatus = async (offer) => {
    try {
      const updatedOffer = { ...offer, active: !offer.active };
      await AdminService.updateOffer(offer.id, { active: updatedOffer.active });
      setOffers(offers.map(o => o.id === offer.id ? updatedOffer : o));
      toast.success(`Offer ${updatedOffer.active ? 'activated' : 'deactivated'}`);
    } catch (error) {
      console.error("Failed to toggle status:", error);
      toast.error("Failed to update status");
    }
  };

  // --- 7. Duplicate Offer ---
  const handleDuplicate = (offer) => {
    setEditingOffer(null);
    setFormData({
      ...initialFormState,
      ...offer,
      name: `${offer.name} (Copy)`,
      id: undefined
    });
    setIsDialogOpen(true);
  };

  // Helper to handle form changes
  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  // Filter offers
  const filteredOffers = offers.filter(offer => {
    const matchesSearch = 
      offer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      offer.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      offer.eligible_category?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const now = new Date();
    const isExpired = offer.valid_to && new Date(offer.valid_to) < now;
    const isUpcoming = offer.valid_from && new Date(offer.valid_from) > now;
    const isActive = offer.active && !isExpired && !isUpcoming;
    
    const matchesStatus = filterStatus === "all" || 
                         (filterStatus === "active" && isActive) ||
                         (filterStatus === "inactive" && !offer.active) ||
                         (filterStatus === "expired" && isExpired) ||
                         (filterStatus === "upcoming" && isUpcoming);
    
    return matchesSearch && matchesStatus;
  });

  // Calculate stats
  const stats = {
    total: offers.length,
    active: offers.filter(o => o.active).length,
    percentage: offers.filter(o => o.discount_type === 'percentage').length,
    fixed: offers.filter(o => o.discount_type === 'fixed').length,
    stackable: offers.filter(o => o.stackable).length,
  };

  // Format currency
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  };

  // Format discount display
  const formatDiscount = (offer) => {
    if (offer.discount_type === 'percentage') {
      return `${offer.discount_value}% OFF`;
    } else {
      return `${formatCurrency(offer.discount_value)} OFF`;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Offers & Discounts</h1>
          <p className="text-muted-foreground">Manage promotional offers and discounts</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={(open) => {
          if (!open) {
            setFormData(initialFormState);
            setEditingOffer(null);
          }
          setIsDialogOpen(open);
        }}>
          <DialogTrigger asChild>
            <Button><Plus className="mr-2 h-4 w-4" /> Create Offer</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingOffer ? 'Edit Offer' : 'Create New Offer'}</DialogTitle>
              <DialogDescription>
                {editingOffer ? 'Update offer details' : 'Create a new promotional offer'}
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4 py-4">
              {/* Basic Information */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Basic Information</h3>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Offer Name *</Label>
                    <Input 
                      id="name"
                      placeholder="e.g. Summer Sale 2024" 
                      value={formData.name} 
                      onChange={(e) => handleChange("name", e.target.value)} 
                      required 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea 
                      id="description"
                      placeholder="Describe this offer..." 
                      value={formData.description} 
                      onChange={(e) => handleChange("description", e.target.value)} 
                      rows={2}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="eligible_category">Eligible Category</Label>
                    <Input 
                      id="eligible_category"
                      placeholder="e.g. Shoes, Clothing, Accessories" 
                      value={formData.eligible_category} 
                      onChange={(e) => handleChange("eligible_category", e.target.value)} 
                    />
                    <p className="text-xs text-muted-foreground">Leave empty for all categories</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Discount Configuration */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Discount Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Discount Type *</Label>
                    <Select 
                      value={formData.discount_type} 
                      onValueChange={(val) => handleChange("discount_type", val)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">
                          <div className="flex items-center gap-2">
                            <Percent className="h-3 w-3" />
                            Percentage (%)
                          </div>
                        </SelectItem>
                        <SelectItem value="fixed">
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-3 w-3" />
                            Fixed Amount
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="discount_value">Discount Value *</Label>
                    <Input 
                      id="discount_value"
                      type="number" 
                      step="0.01"
                      min="0"
                      placeholder={formData.discount_type === 'percentage' ? 'e.g. 20' : 'e.g. 500'} 
                      value={formData.discount_value} 
                      onChange={(e) => handleChange("discount_value", e.target.value)} 
                      required 
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="min_cart_value">Minimum Cart Value (₹)</Label>
                    <Input 
                      id="min_cart_value"
                      type="number" 
                      step="0.01"
                      min="0"
                      placeholder="0 for no minimum"
                      value={formData.min_cart_value} 
                      onChange={(e) => handleChange("min_cart_value", e.target.value)} 
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="max_discount_amount">Maximum Discount Cap (₹)</Label>
                    <Input 
                      id="max_discount_amount"
                      type="number" 
                      step="0.01"
                      min="0"
                      placeholder="0 for no cap"
                      value={formData.max_discount_amount} 
                      onChange={(e) => handleChange("max_discount_amount", e.target.value)} 
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Validity */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Validity Period</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="valid_from">Valid From</Label>
                    <Input 
                      id="valid_from"
                      type="datetime-local" 
                      value={formData.valid_from} 
                      onChange={(e) => handleChange("valid_from", e.target.value)} 
                    />
                    <p className="text-xs text-muted-foreground">Leave empty for immediate start</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="valid_to">Valid To</Label>
                    <Input 
                      id="valid_to"
                      type="datetime-local" 
                      value={formData.valid_to} 
                      onChange={(e) => handleChange("valid_to", e.target.value)} 
                    />
                    <p className="text-xs text-muted-foreground">Leave empty for no expiry</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Settings */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold">Settings</h3>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="stackable">Stackable</Label>
                    <p className="text-sm text-muted-foreground">Can be combined with other offers</p>
                  </div>
                  <Switch 
                    id="stackable"
                    checked={formData.stackable} 
                    onCheckedChange={(checked) => handleChange("stackable", checked)} 
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="active">Active</Label>
                    <p className="text-sm text-muted-foreground">Make this offer available</p>
                  </div>
                  <Switch 
                    id="active"
                    checked={formData.active} 
                    onCheckedChange={(checked) => handleChange("active", checked)} 
                  />
                </div>
              </div>

              <DialogFooter className="pt-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => {
                    setIsDialogOpen(false);
                    setFormData(initialFormState);
                    setEditingOffer(null);
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {editingOffer ? 'Update Offer' : 'Create Offer'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Offers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.active}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">% Discounts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.percentage}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Fixed Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats.fixed}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Stackable</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-indigo-600">{stats.stackable}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search offers by name, description, or category..."
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
              <SelectItem value="all">All Offers</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
              <SelectItem value="expired">Expired</SelectItem>
              <SelectItem value="upcoming">Upcoming</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="icon" title="Refresh" onClick={fetchOffers}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Offers Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Offer Details</TableHead>
              <TableHead>Discount</TableHead>
              <TableHead>Requirements</TableHead>
              <TableHead>Validity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center">
                  <div className="flex items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    Loading offers...
                  </div>
                </TableCell>
              </TableRow>
            ) : filteredOffers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  <div className="flex flex-col items-center justify-center">
                    <Tag className="h-8 w-8 mb-2 opacity-50" />
                    <p>No offers found</p>
                    <p className="text-sm">Try adjusting your search or create a new offer</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              filteredOffers.map((offer) => {
                const now = new Date();
                const validFrom = offer.valid_from ? new Date(offer.valid_from) : null;
                const validTo = offer.valid_to ? new Date(offer.valid_to) : null;
                
                const isExpired = validTo && validTo < now;
                const isUpcoming = validFrom && validFrom > now;
                const isActive = offer.active && !isExpired && !isUpcoming;
                
                return (
                  <TableRow key={offer.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Tag className="h-3 w-3 text-primary" />
                          <span className="font-medium">{offer.name}</span>
                          {offer.stackable && (
                            <Badge variant="outline" className="text-xs">Stackable</Badge>
                          )}
                        </div>
                        {offer.description && (
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            {offer.description}
                          </p>
                        )}
                        {offer.eligible_category && (
                          <Badge variant="secondary" className="text-xs">
                            {offer.eligible_category}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="space-y-1">
                        <Badge variant="secondary" className="text-sm">
                          {formatDiscount(offer)}
                        </Badge>
                        {offer.max_discount_amount > 0 && (
                          <p className="text-xs text-muted-foreground">
                            Max: {formatCurrency(offer.max_discount_amount)}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="space-y-1">
                        {offer.min_cart_value > 0 ? (
                          <p className="text-sm">
                            Min cart: {formatCurrency(offer.min_cart_value)}
                          </p>
                        ) : (
                          <p className="text-sm text-muted-foreground">No minimum</p>
                        )}
                        <div className="flex items-center gap-2">
                          {offer.stackable ? (
                            <div className="flex items-center gap-1 text-green-600">
                              <Check className="h-3 w-3" />
                              <span className="text-xs">Stackable</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1 text-red-600">
                              <X className="h-3 w-3" />
                              <span className="text-xs">Not stackable</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="space-y-1">
                        {validFrom || validTo ? (
                          <div className="text-sm flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {validFrom ? format(validFrom, 'MMM dd, yyyy') : 'Now'}
                            {' → '}
                            {validTo ? format(validTo, 'MMM dd, yyyy') : '∞'}
                          </div>
                        ) : (
                          <Badge variant="outline" className="text-xs">No expiry</Badge>
                        )}
                        {isExpired && (
                          <Badge variant="outline" className="text-xs bg-red-50 text-red-600">
                            Expired
                          </Badge>
                        )}
                        {isUpcoming && (
                          <Badge variant="outline" className="text-xs bg-blue-50 text-blue-600">
                            Upcoming
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${isActive ? 'bg-green-500' : 'bg-gray-300'}`} />
                        <Badge 
                          variant={isActive ? "default" : "secondary"}
                          className="text-xs cursor-pointer hover:opacity-80"
                          onClick={() => handleToggleStatus(offer)}
                        >
                          {isActive ? 'Active' : isExpired ? 'Expired' : isUpcoming ? 'Upcoming' : 'Inactive'}
                        </Badge>
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8"
                          onClick={() => handleEdit(offer)}
                          title="Edit"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8"
                          onClick={() => handleDuplicate(offer)}
                          title="Duplicate"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={() => handleDelete(offer.id)}
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}