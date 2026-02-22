import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertOctagon, MessageSquare, Clock, 
  CheckCircle2, ShieldAlert, ArrowRight, Loader2
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

// --- Helper: Status Styling ---
const getStatusConfig = (status) => {
  const s = (status || 'pending').toLowerCase();
  if (s === 'resolved' || s === 'closed') {
    return { label: 'Resolved', color: 'bg-emerald-50 text-emerald-600 border-emerald-200', icon: CheckCircle2 };
  }
  if (s === 'in_progress' || s === 'investigating') {
    return { label: 'Investigating', color: 'bg-blue-50 text-blue-600 border-blue-200', icon: Clock };
  }
  return { label: 'Pending Action', color: 'bg-amber-50 text-amber-600 border-amber-200', icon: AlertOctagon };
};

export default function UserComplaints({ userId }) {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const res = await AdminUserService.getUserComplaints(userId);
      const fetched = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
      // Sort newest first
      setComplaints(fetched.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)));
    } catch (error) {
      console.error("Failed to load complaints", error);
      toast.error("Could not load user complaints.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (userId) fetchComplaints();
  }, [userId]);

  // --- Update Status Handler ---
  const handleStatusUpdate = async (complaintId, newStatus) => {
    try {
      setUpdatingId(complaintId);
      await AdminUserService.updateUserComplaintStatus(userId, complaintId, { status: newStatus });
      
      // Optimistic UI update
      setComplaints(prev => prev.map(c => 
        c.id === complaintId ? { ...c, status: newStatus } : c
      ));
      
      toast.success(`Complaint marked as ${newStatus.replace('_', ' ')}`);
    } catch (error) {
      console.error("Failed to update status", error);
      toast.error("Could not update the complaint status.");
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2].map(i => (
          <Skeleton key={i} className="h-64 w-full rounded-[2.5rem] bg-zinc-50" />
        ))}
      </div>
    );
  }

  if (complaints.length === 0) {
    return (
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] min-h-[400px] flex flex-col items-center justify-center text-center p-10">
        <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mb-6 border border-emerald-100">
          <ShieldAlert size={32} className="text-emerald-500" strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-serif font-bold text-zinc-900 mb-2">Clean Record</h3>
        <p className="text-zinc-500 max-w-sm">This user hasn't filed any complaints or support tickets. Everything looks great!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <AnimatePresence>
        {complaints.map((complaint, index) => {
          const complaintId = complaint.id || "Unknown";
          const displayId = complaintId.toString().slice(-8).toUpperCase();
          const date = complaint.created_at 
            ? new Date(complaint.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) 
            : 'Unknown Date';
          
          const { label: statusLabel, color: statusColor, icon: StatusIcon } = getStatusConfig(complaint.status);
          const isResolved = (complaint.status || '').toLowerCase() === 'resolved';

          return (
            <motion.div
              key={complaintId}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              className="bg-white rounded-[2rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] p-6 md:p-8 flex flex-col"
            >
              
              {/* Header */}
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-zinc-50 rounded-2xl border border-zinc-100 flex items-center justify-center text-zinc-400 shrink-0">
                    <MessageSquare size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
                        {complaint.subject || complaint.reason || "Support Ticket"}
                      </h3>
                      <span className="text-[10px] font-mono font-bold text-zinc-400 px-2 py-0.5 bg-zinc-50 rounded-md border border-zinc-100">
                        #{displayId}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-zinc-500 flex items-center gap-1.5">
                      <Clock size={12} /> Filed on {date}
                    </p>
                  </div>
                </div>

                <Badge className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest shadow-none border shrink-0 w-fit ${statusColor}`}>
                  <StatusIcon size={12} className="mr-1.5" />
                  {statusLabel}
                </Badge>
              </div>

              {/* Body: Complaint Description */}
              <div className="bg-zinc-50/50 border border-zinc-100 rounded-xl p-5 mb-6 text-sm font-medium text-zinc-700 leading-relaxed italic">
                "{complaint.description || complaint.message || "No description provided."}"
              </div>

              {/* Footer: Admin Actions */}
              <div className="pt-6 border-t border-zinc-50 flex flex-wrap items-center justify-between gap-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">
                  Admin Actions
                </p>
                
                <div className="flex items-center gap-3">
                  {!isResolved && (
                    <>
                      <button 
                        onClick={() => handleStatusUpdate(complaintId, 'in_progress')}
                        disabled={updatingId === complaintId}
                        className="px-4 py-2 text-xs font-bold tracking-wide rounded-full border border-blue-200 text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors disabled:opacity-50 flex items-center gap-2"
                      >
                        {updatingId === complaintId ? <Loader2 size={14} className="animate-spin" /> : "Investigate"}
                      </button>
                      <button 
                        onClick={() => handleStatusUpdate(complaintId, 'resolved')}
                        disabled={updatingId === complaintId}
                        className="px-4 py-2 text-xs font-bold tracking-wide rounded-full bg-zinc-900 text-white hover:bg-black transition-all shadow-md disabled:opacity-50 flex items-center gap-2"
                      >
                        {updatingId === complaintId ? <Loader2 size={14} className="animate-spin" /> : <><CheckCircle2 size={14} /> Resolve Ticket</>}
                      </button>
                    </>
                  )}
                  {isResolved && (
                    <button 
                      onClick={() => handleStatusUpdate(complaintId, 'pending')}
                      disabled={updatingId === complaintId}
                      className="px-4 py-2 text-xs font-bold tracking-wide rounded-full border border-zinc-200 text-zinc-500 hover:bg-zinc-50 transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                       {updatingId === complaintId ? <Loader2 size={14} className="animate-spin" /> : "Reopen Ticket"}
                    </button>
                  )}
                </div>
              </div>

            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}