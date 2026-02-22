import React, { useEffect, useState } from 'react';
import { AdminService } from '@/lib/adminApi';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from "@/components/ui/table";
import { 
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter 
} from "@/components/ui/dialog";
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { 
  Plus, Trash2, Calendar, Loader2, Tag, Edit2, Percent, DollarSign 
} from 'lucide-react';
import { format } from 'date-fns';
import { toast } from "sonner";

export default function DiscountRules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Exact match to ProductDiscountRuleCreate Pydantic Schema
  const initialFormState = {
    name: "",
    discount_type: "percentage",
    value: 0,
    category_filter: "",
    brand_filter: "",
    active: true,
    valid_from: new Date().toISOString().slice(0, 16), // Default to now
    valid_to: ""
  };
  
  const [formData, setFormData] = useState(initialFormState);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const res = await AdminService.listDiscountRules();
      setRules(Array.isArray(res) ? res : []);
    } catch (error) {
      toast.error("Failed to load discount rules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRules(); }, []);

  const prepareFormData = (data) => {
    return {
      name: data.name.trim(),
      discount_type: data.discount_type,
      value: parseFloat(data.value) || 0,
      category_filter: data.category_filter?.trim() || null,
      brand_filter: data.brand_filter?.trim() || null,
      active: Boolean(data.active),
      valid_from: new Date(data.valid_from).toISOString(), // Required by schema
      valid_to: data.valid_to ? new Date(data.valid_to).toISOString() : null,
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = prepareFormData(formData);
      if (editingRule) {
        await AdminService.updateDiscountRule(editingRule.id, payload);
        toast.success("Rule updated successfully");
      } else {
        await AdminService.createDiscountRule(payload);
        toast.success("Rule created successfully");
      }
      setFormData(initialFormState);
      setEditingRule(null);
      setIsDialogOpen(false);
      fetchRules();
    } catch (error) {
      toast.error(`Error saving rule: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this automatic discount rule?")) return;
    try {
      await AdminService.deleteDiscountRule(id);
      setRules(rules.filter(r => r.id !== id));
      toast.success("Rule deleted");
    } catch (error) {
      toast.error("Failed to delete rule");
    }
  };

  const handleEdit = (rule) => {
    setEditingRule(rule);
    setFormData({
      ...initialFormState,
      ...rule,
      valid_from: rule.valid_from ? format(new Date(rule.valid_from), "yyyy-MM-dd'T'HH:mm") : "",
      valid_to: rule.valid_to ? format(new Date(rule.valid_to), "yyyy-MM-dd'T'HH:mm") : "",
    });
    setIsDialogOpen(true);
  };

  const handleChange = (key, value) => setFormData(prev => ({ ...prev, [key]: value }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Automatic Discount Rules</h1>
          <p className="text-muted-foreground">Manage automatic sales and strikethrough pricing</p>
        </div>
        <Button onClick={() => { setFormData(initialFormState); setEditingRule(null); setIsDialogOpen(true); }}>
          <Plus className="mr-2 h-4 w-4" /> New Rule
        </Button>
      </div>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? 'Edit Rule' : 'Create Automatic Sale'}</DialogTitle>
            <DialogDescription>These apply automatically to matching products.</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Internal Sale Name *</Label>
              <Input placeholder="e.g. Summer Sale - Shoes" value={formData.name} onChange={e => handleChange("name", e.target.value)} required />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Discount Type</Label>
                <Select value={formData.discount_type} onValueChange={v => handleChange("discount_type", v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="percentage">Percentage (%)</SelectItem>
                    <SelectItem value="flat">Flat Amount (₹)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Discount Value *</Label>
                <Input type="number" step="0.01" value={formData.value} onChange={e => handleChange("value", e.target.value)} required />
              </div>
            </div>

            <Separator />
            <h3 className="text-sm font-semibold">Target Filters</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Category Filter</Label>
                <Input placeholder="e.g. Shoes" value={formData.category_filter || ''} onChange={e => handleChange("category_filter", e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Brand Filter</Label>
                <Input placeholder="e.g. Nike" value={formData.brand_filter || ''} onChange={e => handleChange("brand_filter", e.target.value)} />
              </div>
            </div>

            <Separator />
            <h3 className="text-sm font-semibold">Timing</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Valid From *</Label>
                <Input type="datetime-local" value={formData.valid_from} onChange={e => handleChange("valid_from", e.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label>Valid To</Label>
                <Input type="datetime-local" value={formData.valid_to || ''} onChange={e => handleChange("valid_to", e.target.value)} />
              </div>
            </div>

            <div className="flex items-center justify-between pt-4">
              <Label>Rule Active</Label>
              <Switch checked={formData.active} onCheckedChange={c => handleChange("active", c)} />
            </div>

            <DialogFooter>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Saving...' : 'Save Rule'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Sale Name</TableHead>
              <TableHead>Discount</TableHead>
              <TableHead>Filters</TableHead>
              <TableHead>Validity</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? <TableRow><TableCell colSpan={6} className="text-center h-24"><Loader2 className="animate-spin h-6 w-6 mx-auto" /></TableCell></TableRow> : 
              rules.map(rule => (
              <TableRow key={rule.id}>
                <TableCell className="font-medium">{rule.name}</TableCell>
                <TableCell><Badge variant="secondary">{rule.discount_type === 'percentage' ? `${rule.value}%` : `₹${rule.value}`}</Badge></TableCell>
                <TableCell>
                  <div className="flex gap-1 flex-col">
                    {rule.category_filter && <span className="text-xs text-muted-foreground">Cat: {rule.category_filter}</span>}
                    {rule.brand_filter && <span className="text-xs text-muted-foreground">Brand: {rule.brand_filter}</span>}
                    {!rule.category_filter && !rule.brand_filter && <span className="text-xs text-muted-foreground">Global (All)</span>}
                  </div>
                </TableCell>
                <TableCell className="text-xs">
                  <div>{format(new Date(rule.valid_from), 'MMM dd, yyyy')}</div>
                  <div className="text-muted-foreground">to {rule.valid_to ? format(new Date(rule.valid_to), 'MMM dd, yyyy') : 'Forever'}</div>
                </TableCell>
                <TableCell><Badge variant={rule.active ? "default" : "destructive"}>{rule.active ? 'Active' : 'Inactive'}</Badge></TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" onClick={() => handleEdit(rule)}><Edit2 className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="sm" className="text-destructive" onClick={() => handleDelete(rule.id)}><Trash2 className="h-4 w-4" /></Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}