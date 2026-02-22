import React, { useState } from 'react';
import { UserAdminService } from "../lib/userApi";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Loader2, TicketPercent, Package, AlertCircle, Truck } from 'lucide-react';

export default function UserActions({ userId, onUpdate }) {
  const [loading, setLoading] = useState(false);
  const [modalType, setModalType] = useState(null); // 'offer', 'order', 'complaint', 'pickup'
  
  // Form States
  const [formData, setFormData] = useState({
    name: '',
    discount_value: '',
    id: '', // Used for Order ID, Complaint ID, or Pickup ID
    status: '',
    reason: '' // Mandatory for Backend Audit Logs
  });

  const resetForm = () => {
    setFormData({ name: '', discount_value: '', id: '', status: '', reason: '' });
    setModalType(null);
  };

  const handleAction = async () => {
    setLoading(true);
    try {
      if (modalType === 'offer') {
        await UserAdminService.createPersonalizedOffer(userId, {
          offer_name: formData.name,
          discount_value: parseFloat(formData.discount_value),
          active: true,
          stackable: false
        });
        toast.success("Personalized offer issued");
      } 
      else if (modalType === 'order') {
        await UserAdminService.updateOrderStatus(userId, formData.id, formData.status, formData.reason);
        toast.success("Order status updated");
      } 
      else if (modalType === 'complaint') {
        await UserAdminService.updateComplaintStatus(userId, formData.id, formData.status, formData.reason);
        toast.success("Complaint resolved");
      }
      
      resetForm();
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error(error.message || "Action failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-2 gap-2 mt-4">
      <Button variant="outline" size="sm" onClick={() => setModalType('offer')}>
        <TicketPercent className="w-4 h-4 mr-2 text-orange-500" /> Issue Reward
      </Button>
      
      <Button variant="outline" size="sm" onClick={() => setModalType('order')}>
        <Package className="w-4 h-4 mr-2 text-blue-500" /> Update Order
      </Button>

      <Button variant="outline" size="sm" onClick={() => setModalType('complaint')}>
        <AlertCircle className="w-4 h-4 mr-2 text-red-500" /> Resolve Ticket
      </Button>

      <Dialog open={!!modalType} onOpenChange={resetForm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="capitalize">{modalType} Management</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4 text-xs">
            {/* Conditional Fields based on Modal Type */}
            {modalType === 'offer' ? (
              <>
                <div className="space-y-2">
                  <Label>Offer Name</Label>
                  <Input placeholder="e.g. Loyalty Bonus" onChange={e => setFormData({...formData, name: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Discount Value (₹)</Label>
                  <Input type="number" onChange={e => setFormData({...formData, discount_value: e.target.value})} />
                </div>
              </>
            ) : (
              <>
                <div className="space-y-2">
                  <Label>Target ID ({modalType} ID)</Label>
                  <Input placeholder={`Enter ${modalType} UUID`} onChange={e => setFormData({...formData, id: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>New Status</Label>
                  <Select onValueChange={(val) => setFormData({...formData, status: val})}>
                    <SelectTrigger><SelectValue placeholder="Select Status" /></SelectTrigger>
                    <SelectContent>
                      {modalType === 'order' && ["processing", "shipped", "delivered", "cancelled"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                      {modalType === 'complaint' && ["open", "resolved", "closed"].map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {/* Reason Field - Required by Backend for Audit Logs */}
            <div className="space-y-2">
              <Label>Reason / Note (Audit Log)</Label>
              <Textarea 
                placeholder="Required for administrative tracking..." 
                className="h-20"
                onChange={e => setFormData({...formData, reason: e.target.value})}
              />
            </div>
          </div>

          <DialogFooter>
            <Button onClick={handleAction} disabled={loading || !formData.reason}>
              {loading && <Loader2 className="animate-spin mr-2 h-4 w-4" />} 
              Confirm Action
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}