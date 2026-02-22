import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bot, BrainCircuit, Activity, Zap, 
  Clock, Hash, ArrowRight, ShieldCheck, Database
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

// --- Helper: Format Decision Type ---
const formatDecisionType = (type) => {
  if (!type) return 'Unknown Action';
  return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};

export default function UserAgentData({ userId }) {
  const [runs, setRuns] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgentData = async () => {
      try {
        setLoading(true);
        const [runsRes, decisionsRes] = await Promise.all([
          AdminUserService.getUserAgentRuns(userId).catch(() => []),
          AdminUserService.getUserAgentDecisions(userId).catch(() => [])
        ]);

        const fetchedRuns = Array.isArray(runsRes?.data) ? runsRes.data : (Array.isArray(runsRes) ? runsRes : []);
        const fetchedDecisions = Array.isArray(decisionsRes?.data) ? decisionsRes.data : (Array.isArray(decisionsRes) ? decisionsRes : []);

        setRuns(fetchedRuns.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)));
        setDecisions(fetchedDecisions.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)));
      } catch (error) {
        console.error("Failed to load agent data", error);
        toast.error("Could not load the AI Agent history.");
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchAgentData();
  }, [userId]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <Skeleton className="h-[600px] w-full rounded-[2.5rem] bg-zinc-50" />
        </div>
        <div className="lg:col-span-2">
          <Skeleton className="h-[600px] w-full rounded-[2.5rem] bg-zinc-50" />
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      {/* ========================================= */}
      {/* LEFT: AGENT RUNS (1/3 Width)              */}
      {/* ========================================= */}
      <div className="lg:col-span-1 bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] overflow-hidden flex flex-col">
        <div className="p-8 border-b border-zinc-50 bg-indigo-50/30 flex items-center gap-4">
          <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center border border-indigo-100 text-indigo-600 shadow-sm">
            <Activity size={20} />
          </div>
          <div>
            <h3 className="text-2xl font-serif font-bold text-zinc-900">Agent Runs</h3>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-400 mt-1">Execution Cycles</p>
          </div>
        </div>

        <div className="p-6 flex-1 bg-zinc-50/10 overflow-y-auto max-h-[600px] custom-scrollbar">
          {runs.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-10 opacity-60">
              <Bot size={32} className="text-zinc-300 mb-4" strokeWidth={1.5} />
              <p className="text-sm font-bold text-zinc-900 mb-1">No execution runs</p>
              <p className="text-zinc-400 text-xs">The AI hasn't triggered specific standalone runs for this user.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {runs.map((run, index) => {
                  const date = run.created_at ? new Date(run.created_at).toLocaleString() : 'Unknown';
                  return (
                    <motion.div
                      key={run.id || index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-5 rounded-2xl border border-zinc-100 bg-white shadow-sm flex flex-col gap-3"
                    >
                      <div className="flex items-center justify-between">
                        <Badge className="bg-indigo-50 text-indigo-600 border-indigo-100 shadow-none text-[10px] font-bold uppercase tracking-widest px-2 py-1">
                          Completed
                        </Badge>
                        <span className="text-[10px] font-mono text-zinc-400">{run.id?.split('-')[0].toUpperCase()}</span>
                      </div>
                      <p className="text-xs font-medium text-zinc-500 flex items-center gap-1.5">
                        <Clock size={12} className="text-zinc-400" /> {date}
                      </p>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* ========================================= */}
      {/* RIGHT: AGENT DECISIONS (2/3 Width)        */}
      {/* ========================================= */}
      <div className="lg:col-span-2 bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] overflow-hidden flex flex-col">
        <div className="p-8 border-b border-zinc-50 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-violet-50 rounded-2xl flex items-center justify-center border border-violet-100 text-violet-600">
              <BrainCircuit size={20} />
            </div>
            <div>
              <h3 className="text-2xl font-serif font-bold text-zinc-900">AI Decisions</h3>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-400 mt-1">Autonomous Actions</p>
            </div>
          </div>
          <Badge className="bg-zinc-100 text-zinc-500 border-none shadow-none">{decisions.length} Records</Badge>
        </div>

        <div className="p-6 md:p-8 flex-1 overflow-y-auto max-h-[600px] custom-scrollbar">
          {decisions.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-10">
              <ShieldCheck size={40} className="text-zinc-200 mb-4" strokeWidth={1.5} />
              <p className="text-lg font-bold text-zinc-900 mb-1">No autonomous decisions</p>
              <p className="text-zinc-500 text-sm max-w-[300px]">The Daksha AI engine hasn't recorded any specific systemic decisions related to this user profile yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {decisions.map((decision, index) => {
                  const date = decision.created_at ? new Date(decision.created_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Unknown Date';
                  const entityType = decision.decision_output?.entity_type || 'system';
                  const source = decision.decision_output?.source || 'ai';

                  return (
                    <motion.div
                      key={decision.id || index}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="group p-5 md:p-6 rounded-2xl border border-zinc-100 bg-zinc-50/50 hover:bg-white hover:shadow-lg transition-all duration-300"
                    >
                      
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-violet-100 text-violet-600 flex items-center justify-center shrink-0">
                            <Zap size={16} className="fill-violet-200" />
                          </div>
                          <div>
                            <h4 className="font-bold text-zinc-900 text-base tracking-tight">
                              {formatDecisionType(decision.decision_type)}
                            </h4>
                            <p className="text-xs font-medium text-zinc-400 flex items-center gap-1.5 mt-0.5">
                              <Clock size={12} /> {date}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <Badge className="bg-white text-zinc-500 border border-zinc-200 shadow-sm text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 flex items-center gap-1">
                            <Database size={10} /> {entityType}
                          </Badge>
                          <Badge className="bg-zinc-900 text-white border-none shadow-none text-[10px] font-bold uppercase tracking-widest px-2.5 py-1">
                            {source}
                          </Badge>
                        </div>
                      </div>

                      {/* AI Rationale & Details */}
                      <div className="bg-white border border-zinc-100 rounded-xl p-4 flex flex-col gap-2">
                        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-400 flex items-center gap-1.5">
                          <BrainCircuit size={12} /> AI Rationale
                        </p>
                        <p className="text-sm font-medium text-zinc-700 italic border-l-2 border-violet-200 pl-3 py-1">
                          "{decision.rationale || 'No rationale provided by the engine.'}"
                        </p>
                        
                        {/* Technical Output Details */}
                        <div className="mt-2 pt-3 border-t border-zinc-50 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Hash size={12} className="text-zinc-300" />
                            <span className="text-[10px] font-mono text-zinc-400">ID: {decision.id?.split('-')[0].toUpperCase()}</span>
                          </div>
                          {decision.decision_output?.entity_id && (
                            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-zinc-400 bg-zinc-50 px-2 py-1 rounded-md">
                              Entity <ArrowRight size={10} /> {decision.decision_output.entity_id.split('-')[0].toUpperCase()}
                            </div>
                          )}
                        </div>
                      </div>

                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}