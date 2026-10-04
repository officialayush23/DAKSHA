// src/admin/pages/AgentOps.jsx
// Staff console for the orchestration engine:
//   • approvals the agents are waiting on (high-value refunds, proactive marketing ...)
//   • what each agent remembers about a customer (private, per-agent memory)
//   • proactive follow-ups: run now + recent outcomes
//   • the live LangGraph (Mermaid source)
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { CheckCircle2, XCircle, RefreshCw, Brain, Zap, GitBranch, Loader2, Bell } from 'lucide-react';
import { apiClient } from '@/lib/adminApi';
import { getAccessToken, wsBase } from '@/lib/authToken';

const Section = ({ icon: Icon, title, action, children }) => (
  <div className="rounded-2xl border border-zinc-200 bg-white p-5 space-y-3">
    <div className="flex items-center justify-between">
      <h2 className="flex items-center gap-2 font-semibold text-zinc-800"><Icon size={18} /> {title}</h2>
      {action}
    </div>
    {children}
  </div>
);

export default function AgentOps() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(null);
  const [userId, setUserId] = useState('');
  const [memories, setMemories] = useState(null);
  const [proactive, setProactive] = useState([]);
  const [running, setRunning] = useState(false);
  const [graph, setGraph] = useState('');
  const lobby = useRef(null);

  const loadApprovals = useCallback(async () => {
    setLoading(true);
    try { setApprovals(await apiClient('/admin/agentic/approvals')); }
    catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  }, []);

  const loadProactive = useCallback(async () => {
    try { setProactive(await apiClient('/admin/agentic/proactive/recent')); } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    loadApprovals();
    loadProactive();
    apiClient('/admin/agentic/graph').then(r => setGraph(r.mermaid)).catch(() => {});
    // live pings: new approvals / handoffs
    (async () => {
      const token = await getAccessToken();
      if (!token) return;
      const ws = new WebSocket(`${wsBase()}/ws/admin/lobby?token=${encodeURIComponent(token)}`);
      lobby.current = ws;
      ws.onmessage = (ev) => {
        const d = JSON.parse(ev.data);
        if (d.type === 'approval_requested') { toast.info(`Approval needed: ${d.summary}`); loadApprovals(); }
        if (d.type === 'handoff_opened') toast.info('A customer asked for a human (see Agent Handoffs)');
      };
    })();
    return () => lobby.current?.close();
  }, [loadApprovals, loadProactive]);

  const decide = async (a, approved) => {
    setBusy(a.id);
    try {
      const r = await apiClient(`/admin/agentic/approvals/${a.id}/decide`, 'POST', { approved });
      toast.success(approved ? 'Approved — the agent continued' : 'Rejected');
      if (r?.result?.reply) toast.message(r.result.reply.slice(0, 160));
      loadApprovals();
    } catch (e) { toast.error(e.message); }
    finally { setBusy(null); }
  };

  const loadMemories = async () => {
    if (!userId.trim()) return;
    try { setMemories(await apiClient(`/admin/agentic/memories/${userId.trim()}`)); }
    catch (e) { toast.error(e.message); }
  };

  const runProactive = async () => {
    setRunning(true);
    try {
      const r = await apiClient('/admin/agentic/proactive/run', 'POST');
      toast.success(`Scan done: ${r.triggers} trigger(s), ${r.released_holds} expired hold(s) released`);
      loadProactive(); loadApprovals();
    } catch (e) { toast.error(e.message); }
    finally { setRunning(false); }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Agent Ops</h1>
        <p className="text-zinc-500 text-sm">Human-in-the-loop approvals, per-agent memory and proactive automation.</p>
      </div>

      <Section icon={Bell} title={`Waiting for approval (${approvals.length})`}
        action={<button onClick={loadApprovals} className="text-zinc-500 hover:text-black"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /></button>}>
        {approvals.length === 0 && <p className="text-sm text-zinc-400">Nothing waiting.</p>}
        <div className="space-y-2">
          {approvals.map(a => (
            <div key={a.id} className="flex items-start justify-between gap-4 border border-zinc-100 rounded-xl p-3">
              <div className="text-sm">
                <div className="font-medium">{a.summary || `${a.agent} → ${a.tool}`}</div>
                <div className="text-zinc-500 text-xs mt-0.5">
                  {a.customer_name || a.user_id} · rule <code>{a.rule}</code> · {new Date(a.created_at).toLocaleString()}
                </div>
                <pre className="text-[11px] text-zinc-500 mt-1 whitespace-pre-wrap">{JSON.stringify(a.args)}</pre>
              </div>
              <div className="flex gap-2 shrink-0">
                <button disabled={busy === a.id} onClick={() => decide(a, true)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-sm disabled:opacity-50">
                  {busy === a.id ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />} Approve
                </button>
                <button disabled={busy === a.id} onClick={() => decide(a, false)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-zinc-100 text-zinc-700 text-sm disabled:opacity-50">
                  <XCircle size={14} /> Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section icon={Brain} title="Agent memory (per agent, per customer)">
        <div className="flex gap-2">
          <input value={userId} onChange={e => setUserId(e.target.value)} placeholder="customer user id"
            className="flex-1 border border-zinc-200 rounded-lg px-3 py-2 text-sm" />
          <button onClick={loadMemories} className="px-4 py-2 rounded-lg bg-black text-white text-sm">Show</button>
        </div>
        {memories && Object.keys(memories).length === 0 && <p className="text-sm text-zinc-400">No memories yet.</p>}
        {memories && Object.entries(memories).map(([agent, rows]) => (
          <div key={agent} className="border border-zinc-100 rounded-xl p-3">
            <div className="font-medium text-sm capitalize">{agent.replace('_', ' ')} agent · {rows.length}</div>
            <ul className="mt-1 space-y-0.5">
              {rows.slice(0, 8).map((m, i) => <li key={i} className="text-xs text-zinc-600">[{m.kind}] {m.content}</li>)}
            </ul>
          </div>
        ))}
      </Section>

      <Section icon={Zap} title="Proactive follow-ups"
        action={<button onClick={runProactive} disabled={running} className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-black text-white text-sm disabled:opacity-50">
          {running ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />} Run now</button>}>
        {proactive.length === 0 && <p className="text-sm text-zinc-400">No proactive runs yet.</p>}
        <div className="space-y-1">
          {proactive.slice(0, 20).map(p => (
            <div key={p.key} className="text-xs flex justify-between border-b border-zinc-50 py-1">
              <span>{p.type} · {p.key.split(':').slice(1, 2).join('').slice(0, 8)}</span>
              <span className="text-zinc-500">{p.status} · {new Date(p.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </Section>

      <Section icon={GitBranch} title="Orchestration graph (LangGraph)">
        <p className="text-xs text-zinc-500">Paste into mermaid.live to render.</p>
        <pre className="text-[11px] bg-zinc-50 rounded-xl p-3 max-h-72 overflow-auto">{graph || 'loading…'}</pre>
      </Section>
    </div>
  );
}
