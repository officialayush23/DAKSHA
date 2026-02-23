import React, { useEffect, useState } from 'react';
import { AdminService } from '@/lib/adminApi';
import { toast } from 'sonner';

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { CreditCard, AlertTriangle, CheckCircle2, Loader2, Save, Activity, Server, Bot } from 'lucide-react';

export default function PaymentGatewayConfig() {
  // The actual state on the server (from GET)
  const [liveStatus, setLiveStatus] = useState("normal");
  // The state selected in the dropdown (for POST)
  const [draftStatus, setDraftStatus] = useState("normal");
  
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // 1. GET: Fetch the current live condition
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await AdminService.getPaymentGatewayConfig();
        const currentCondition = res.force_status === 'fail' ? 'fail' : 'normal';
        
        setLiveStatus(currentCondition);
        setDraftStatus(currentCondition); // Sync dropdown with live status initially
        setLastUpdated(res.updated_at);
      } catch (error) {
        toast.error("Failed to load payment gateway config");
      } finally {
        setLoading(false);
      }
    };
    
    fetchConfig();
  }, []);

  // 2. POST: Save the updated config
  const handleSave = async () => {
    setSaving(true);
    try {
      // API expects 'fail' to simulate failure, or null/empty to clear it
      const payloadStatus = draftStatus === 'fail' ? 'fail' : ''; 
      
      const res = await AdminService.setPaymentGatewayConfig(payloadStatus);
      const newCondition = res.force_status === 'fail' ? 'fail' : 'normal';
      
      setLiveStatus(newCondition);
      setDraftStatus(newCondition);
      setLastUpdated(res.updated_at || new Date().toISOString());
      
      toast.success(
        newCondition === 'fail' 
          ? "Agent simulation set to REJECT." 
          : "Agent simulation set to NORMAL."
      );
    } catch (error) {
      toast.error("Failed to update payment configuration");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full max-w-4xl rounded-[2rem] border-zinc-100 shadow-sm animate-pulse h-64 bg-zinc-50" />
    );
  }

  const isLiveFailing = liveStatus === 'fail';
  const hasUnsavedChanges = liveStatus !== draftStatus;

  return (
    <Card className="w-full max-w-4xl border-zinc-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-[2rem] overflow-hidden bg-white">
      <CardHeader className="pt-8 pb-6 border-b border-zinc-100">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-zinc-100 text-zinc-900">
            <Bot size={24} />
          </div>
          <div>
            <CardTitle className="text-2xl font-serif text-zinc-900 tracking-tight">AI Agent Payment Config</CardTitle>
            <CardDescription className="text-zinc-500 font-medium mt-1">
              Control how the AI Agent handles payment responses and handoffs globally.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="p-0 flex flex-col md:flex-row">
        
        {/* ================= LEFT SIDE: LIVE CONDITION (GET) ================= */}
        <div className="flex-1 p-8 md:p-10 bg-zinc-50/50 md:border-r border-zinc-100 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={16} className="text-zinc-400" />
            <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">Current Agent Status</h3>
          </div>

          <div className={`p-6 rounded-2xl border-2 flex flex-col gap-3 transition-colors duration-500 ${
            isLiveFailing 
              ? 'bg-red-50 border-red-200' 
              : 'bg-emerald-50 border-emerald-200'
          }`}>
            <div className="flex items-center gap-3">
              {/* Live Pulsing Dot */}
              <span className="relative flex h-4 w-4">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isLiveFailing ? 'bg-red-400' : 'bg-emerald-400'}`}></span>
                <span className={`relative inline-flex rounded-full h-4 w-4 ${isLiveFailing ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
              </span>
              
              <span className={`text-xl font-bold tracking-tight ${isLiveFailing ? 'text-red-700' : 'text-emerald-700'}`}>
                {isLiveFailing ? "Simulating Agent Rejection" : "Normal Agent Processing"}
              </span>
            </div>
            
            <p className={`text-sm font-medium ${isLiveFailing ? 'text-red-600/80' : 'text-emerald-600/80'}`}>
              {isLiveFailing 
                ? "The system is currently forcing all payments to fail to simulate transactions being rejected by the AI Agent." 
                : "The AI Agent is currently allowing real transactions to process normally without forced failures."}
            </p>
          </div>

          {lastUpdated && (
            <p className="text-[10px] uppercase tracking-widest text-zinc-400 font-bold mt-6 flex items-center gap-1.5">
              <Server size={12} /> Last synced: {new Date(lastUpdated).toLocaleString()}
            </p>
          )}
        </div>

        {/* ================= RIGHT SIDE: CONTROLS (POST) ================= */}
        <div className="flex-1 p-8 md:p-10 flex flex-col justify-center">
          <div className="space-y-6">
            
            <div>
              <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-900 mb-1">Update Configuration</h3>
              <p className="text-sm text-zinc-500 font-medium mb-4">Override the AI Agent's current payment behavior.</p>
              
              <Select value={draftStatus} onValueChange={setDraftStatus}>
                <SelectTrigger className={`h-14 rounded-xl border-2 text-sm font-bold tracking-wide focus:ring-0 transition-colors ${
                  hasUnsavedChanges ? 'border-amber-400 bg-amber-50 text-amber-900' : 'border-zinc-200'
                }`}>
                  <SelectValue placeholder="Select agent mode" />
                </SelectTrigger>
                <SelectContent className="rounded-xl border-zinc-100 shadow-lg">
                  <SelectItem value="normal" className="focus:bg-emerald-50 focus:text-emerald-700 cursor-pointer">
                    <div className="flex items-center gap-2.5 font-bold py-1 text-emerald-700">
                      <CheckCircle2 size={16} />
                      Normal Processing (Success)
                    </div>
                  </SelectItem>
                  <SelectItem value="fail" className="focus:bg-red-50 focus:text-red-700 cursor-pointer">
                    <div className="flex items-center gap-2.5 font-bold py-1 text-red-600">
                      <AlertTriangle size={16} />
                      Force Agent Rejection (Fail)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button 
              onClick={handleSave} 
              disabled={saving || !hasUnsavedChanges}
              className="w-full h-14 rounded-xl bg-zinc-900 hover:bg-black text-white text-xs font-bold tracking-[0.15em] uppercase shadow-md transition-all active:scale-95 disabled:opacity-50 disabled:bg-zinc-200 disabled:text-zinc-400 disabled:shadow-none"
            >
              {saving ? <Loader2 size={16} className="animate-spin mr-2" /> : <Save size={16} className="mr-2" />}
              {hasUnsavedChanges ? "Apply Override" : "No Changes to Save"}
            </Button>

          </div>
        </div>

      </CardContent>
    </Card>
  );
}