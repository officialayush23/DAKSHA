// src/admin/pages/AgentRuns.jsx — Full agent run trace viewer
import React, { useEffect, useState, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  RefreshCw, Loader2, ChevronRight, ChevronDown,
  CheckCircle, XCircle, Clock, Cpu, Zap
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const authH = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

function agentColor(name) {
  const map = {
    RecommendationAgent: 'text-violet-400 bg-violet-500/10 border-violet-500/30',
    CartAgent:           'text-blue-400 bg-blue-500/10 border-blue-500/30',
    OfferAgent:          'text-amber-400 bg-amber-500/10 border-amber-500/30',
    PaymentAgent:        'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    DeliveryAgent:       'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
    PostPurchaseAgent:   'text-orange-400 bg-orange-500/10 border-orange-500/30',
    SupportAgent:        'text-pink-400 bg-pink-500/10 border-pink-500/30',
    Orchestrator:        'text-zinc-300 bg-zinc-500/10 border-zinc-500/30',
  };
  return map[name] || 'text-zinc-400 bg-zinc-500/10 border-zinc-500/30';
}

function ToolCallRow({ action }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border border-zinc-800 rounded-lg mb-1.5 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-zinc-800/50 transition-colors"
      >
        {action.success
          ? <CheckCircle className="h-3.5 w-3.5 text-emerald-400 flex-shrink-0"/>
          : <XCircle    className="h-3.5 w-3.5 text-red-400 flex-shrink-0"/>}
        <code className="text-xs text-blue-300 font-mono flex-1">{action.tool_name}</code>
        {action.model_used && (
          <span className="text-[10px] text-zinc-600 flex items-center gap-1">
            <Cpu className="h-3 w-3"/>{action.model_used.split('-').slice(0,2).join('-')}
          </span>
        )}
        {action.latency_ms != null && (
          <span className="text-[10px] text-zinc-500 flex items-center gap-1 ml-2">
            <Zap className="h-3 w-3"/>{action.latency_ms}ms
          </span>
        )}
        {expanded ? <ChevronDown className="h-3 w-3 text-zinc-500 ml-2"/> : <ChevronRight className="h-3 w-3 text-zinc-500 ml-2"/>}
      </button>
      {expanded && (
        <div className="px-3 pb-3 space-y-2 bg-zinc-900/60">
          {action.tool_input && (
            <div>
              <p className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1">Input</p>
              <pre className="text-[11px] text-zinc-300 bg-zinc-800/80 rounded p-2 overflow-auto max-h-40 whitespace-pre-wrap">
                {JSON.stringify(action.tool_input, null, 2)}
              </pre>
            </div>
          )}
          {action.tool_output && (
            <div>
              <p className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1">Output</p>
              <pre className="text-[11px] text-zinc-300 bg-zinc-800/80 rounded p-2 overflow-auto max-h-40 whitespace-pre-wrap">
                {JSON.stringify(action.tool_output, null, 2)}
              </pre>
            </div>
          )}
          {action.error_message && (
            <p className="text-xs text-red-400 bg-red-500/10 rounded p-2">{action.error_message}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function AgentRuns() {
  const [runs, setRuns]               = useState([]);
  const [total, setTotal]             = useState(0);
  const [loading, setLoading]         = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);
  const [actions, setActions]         = useState([]);
  const [actionsLoading, setActionsLoading] = useState(false);
  const [filterAgent, setFilterAgent] = useState('');
  const [recentActions, setRecentActions] = useState([]);
  const [tab, setTab]                 = useState('runs'); // runs | live

  const fetchRuns = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: 50 });
      if (filterAgent) params.set('agent_name', filterAgent);
      const res  = await fetch(`${API_BASE}/admin/agent-runs?${params}`, { headers: authH() });
      const data = await res.json();
      setRuns(data.runs || []);
      setTotal(data.total || 0);
    } catch { toast.error('Could not load agent runs'); }
    finally  { setLoading(false); }
  }, [filterAgent]);

  const fetchRecentActions = useCallback(async () => {
    try {
      const res  = await fetch(`${API_BASE}/admin/agent-runs/actions/recent?limit=100`, { headers: authH() });
      const data = await res.json();
      setRecentActions(Array.isArray(data) ? data : []);
    } catch {}
  }, []);

  useEffect(() => { fetchRuns(); }, [fetchRuns]);
  useEffect(() => { fetchRecentActions(); const t = setInterval(fetchRecentActions, 10000); return () => clearInterval(t); }, [fetchRecentActions]);

  const openRun = async (run) => {
    setSelectedRun(run);
    setActionsLoading(true);
    try {
      const res  = await fetch(`${API_BASE}/admin/agent-runs/${run.id}/actions`, { headers: authH() });
      const data = await res.json();
      setActions(data.actions || []);
    } catch { toast.error('Could not load actions'); }
    finally  { setActionsLoading(false); }
  };

  const AGENTS = ['RecommendationAgent','CartAgent','OfferAgent','PaymentAgent','DeliveryAgent','PostPurchaseAgent','SupportAgent'];

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">Agent Runs</h1>
          <p className="text-xs text-zinc-500 mt-0.5">{total} total runs</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterAgent}
            onChange={e => setFilterAgent(e.target.value)}
            className="text-xs bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-zinc-300"
          >
            <option value="">All agents</option>
            {AGENTS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <Button variant="ghost" size="icon" onClick={() => { fetchRuns(); fetchRecentActions(); }}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`}/>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-zinc-900 rounded-lg p-1 w-fit">
        {['runs','live'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-1.5 text-xs rounded-md transition-colors capitalize ${tab===t ? 'bg-zinc-700 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'}`}>
            {t === 'live' ? '⚡ Live Feed' : '📋 Run History'}
          </button>
        ))}
      </div>

      {tab === 'live' ? (
        /* ── LIVE FEED ─────────────────────────────────────────────────── */
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-zinc-300">Recent Tool Calls — live (refreshes every 10s)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1.5">
              {recentActions.map((a) => (
                <div key={a.id} className="flex items-center gap-3 py-1.5 border-b border-zinc-800/60 last:border-0">
                  {a.success ? <CheckCircle className="h-3 w-3 text-emerald-400 flex-shrink-0"/> : <XCircle className="h-3 w-3 text-red-400 flex-shrink-0"/>}
                  <Badge className={`text-[10px] px-1.5 py-0 border flex-shrink-0 ${agentColor(a.agent_name)}`}>{a.agent_name}</Badge>
                  <code className="text-xs text-blue-300 font-mono flex-1 truncate">{a.tool_name}</code>
                  {a.model_used && <span className="text-[10px] text-zinc-600 truncate hidden md:block">{a.model_used.split('-').slice(0,2).join('-')}</span>}
                  {a.latency_ms != null && <span className="text-[10px] text-zinc-500 flex-shrink-0">{a.latency_ms}ms</span>}
                  <span className="text-[10px] text-zinc-600 flex-shrink-0">
                    {a.created_at ? formatDistanceToNow(new Date(a.created_at), { addSuffix: true }) : ''}
                  </span>
                </div>
              ))}
              {!recentActions.length && <p className="text-sm text-zinc-600 text-center py-8">No recent tool calls</p>}
            </div>
          </CardContent>
        </Card>
      ) : (
        /* ── RUN HISTORY ────────────────────────────────────────────────── */
        <div className="flex gap-4">
          {/* Run list */}
          <div className="w-72 flex-shrink-0">
            <ScrollArea className="h-[calc(100vh-14rem)]">
              {loading ? (
                <div className="flex items-center justify-center h-32"><Loader2 className="h-5 w-5 animate-spin text-zinc-500"/></div>
              ) : runs.map(run => (
                <div key={run.id} onClick={() => openRun(run)}
                  className={`mb-1.5 p-3 rounded-lg cursor-pointer border transition-all ${selectedRun?.id === run.id ? 'border-violet-500/60 bg-violet-950/20' : 'border-zinc-800 hover:border-zinc-600 bg-zinc-900/50'}`}>
                  <div className="flex items-center justify-between gap-2">
                    <Badge className={`text-[10px] px-1.5 py-0 border ${agentColor(run.agent_name)}`}>{run.agent_name || 'Unknown'}</Badge>
                    {run.status === 'completed' ? <CheckCircle className="h-3 w-3 text-emerald-400"/> : <XCircle className="h-3 w-3 text-red-400"/>}
                  </div>
                  <p className="text-[10px] text-zinc-600 mt-1.5 font-mono truncate">{run.id?.slice(0,16)}…</p>
                  <div className="flex items-center gap-2 mt-1">
                    {run.duration_ms && <span className="text-[10px] text-zinc-500 flex items-center gap-1"><Zap className="h-2.5 w-2.5"/>{run.duration_ms}ms</span>}
                    <span className="text-[10px] text-zinc-600 flex items-center gap-1">
                      <Clock className="h-2.5 w-2.5"/>
                      {run.started_at ? formatDistanceToNow(new Date(run.started_at), { addSuffix: true }) : ''}
                    </span>
                  </div>
                </div>
              ))}
            </ScrollArea>
          </div>

          {/* Action trace */}
          <div className="flex-1">
            {selectedRun ? (
              <Card className="border-zinc-800 bg-zinc-900/40">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <Badge className={`text-xs border ${agentColor(selectedRun.agent_name)}`}>{selectedRun.agent_name}</Badge>
                      <p className="text-[10px] text-zinc-600 mt-1 font-mono">{selectedRun.id}</p>
                    </div>
                    <div className="text-right">
                      {selectedRun.duration_ms && <p className="text-xs text-zinc-400">{selectedRun.duration_ms}ms total</p>}
                      <p className="text-[10px] text-zinc-600">{selectedRun.started_at ? format(new Date(selectedRun.started_at), 'MMM d, HH:mm:ss') : ''}</p>
                    </div>
                  </div>
                </CardHeader>
                <Separator className="bg-zinc-800"/>
                <CardContent className="pt-4">
                  {actionsLoading ? (
                    <div className="flex items-center justify-center h-32"><Loader2 className="h-5 w-5 animate-spin text-zinc-500"/></div>
                  ) : actions.length === 0 ? (
                    <p className="text-sm text-zinc-600 text-center py-8">No tool calls recorded for this run</p>
                  ) : (
                    <ScrollArea className="h-[calc(100vh-22rem)]">
                      <p className="text-xs text-zinc-600 mb-3">{actions.length} tool call{actions.length !== 1 ? 's' : ''}</p>
                      {actions.map((a, i) => (
                        <div key={a.id} className="flex gap-2">
                          <div className="flex flex-col items-center">
                            <div className="w-5 h-5 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[9px] text-zinc-500 flex-shrink-0">{i+1}</div>
                            {i < actions.length - 1 && <div className="w-px flex-1 bg-zinc-800 my-1"/>}
                          </div>
                          <div className="flex-1 mb-1">
                            <ToolCallRow action={a}/>
                          </div>
                        </div>
                      ))}
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            ) : (
              <div className="flex items-center justify-center h-64 text-zinc-600 text-sm">
                Select a run to see the tool call trace
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
