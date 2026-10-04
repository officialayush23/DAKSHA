// src/components/agent/AgentExtras.jsx
// Small renderers for what the orchestration graph returns besides text:
// the plan/trace ("how I handled this"), a confirm/decline card for actions that
// need the customer's OK, and cart / order / offer cards.
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ShieldCheck, ShieldAlert, Wrench, Brain, CheckCircle2, XCircle, Clock, Package, Tag } from 'lucide-react';

const AGENT_LABEL = {
  discovery: 'Discovery', cart: 'Cart', checkout: 'Checkout', offers: 'Offers', fulfillment: 'Fulfilment',
  post_purchase: 'Post-purchase', support: 'Support', engagement: 'Engagement',
};
export const agentLabel = (a) => AGENT_LABEL[a] || a || 'Orchestrator';

export function PlanTrace({ plan = [], trace = [], latencyMs }) {
  const [open, setOpen] = useState(false);
  if (!plan.length && !trace.length) return null;
  const steps = trace.filter(t => ['planner', 'policy_gate', 'execute', 'human_approval', 'reflect', 'handoff'].includes(t.node)
    || (t.node || '').startsWith('agent_'));
  return (
    <div className="w-full max-w-[600px] text-xs">
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1.5 text-zinc-400 hover:text-zinc-700 transition-colors">
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <Brain size={12} />
        <span>How I handled this</span>
        {plan.length > 0 && <span className="text-zinc-300">· {plan.map(p => agentLabel(p.agent)).join(' → ')}</span>}
        {latencyMs ? <span className="text-zinc-300">· {(latencyMs / 1000).toFixed(1)}s</span> : null}
      </button>
      {open && (
        <div className="mt-2 border border-zinc-100 rounded-xl bg-white p-3 space-y-1.5">
          {plan.map((p, i) => (
            <div key={`p${i}`} className="flex items-start gap-2">
              {p.status === 'done' ? <CheckCircle2 size={12} className="text-emerald-500 mt-0.5" />
                : p.status === 'failed' ? <XCircle size={12} className="text-red-500 mt-0.5" />
                : <Clock size={12} className="text-amber-500 mt-0.5" />}
              <span><b>{agentLabel(p.agent)}</b>: {p.objective}</span>
            </div>
          ))}
          <div className="pt-1.5 border-t border-zinc-100 space-y-1 text-zinc-500 font-mono text-[11px]">
            {steps.map((t, i) => {
              if (t.node === 'planner') return <div key={i}>plan · {t.reasoning || (t.direct ? 'direct reply' : '')}</div>;
              if (t.node === 'policy_gate') return (
                <div key={i} className="flex items-center gap-1">
                  {t.verdict === 'deny' ? <ShieldAlert size={11} className="text-red-500" /> : <ShieldCheck size={11} className="text-emerald-600" />}
                  policy · {t.tool} → {t.verdict}{t.rule ? ` (${t.rule})` : ''}{t.reason ? `: ${t.reason}` : ''}
                </div>);
              if (t.node === 'execute') return (
                <div key={i} className="flex items-center gap-1"><Wrench size={11} />{t.tool} · {t.ok ? 'ok' : 'failed'} · {Math.round(t.ms || 0)}ms</div>);
              if (t.node === 'human_approval') return <div key={i}>approval · {t.approved ? 'approved' : 'declined'}</div>;
              if (t.node === 'reflect') return <div key={i}>critic · step {t.step} {t.verdict}{t.critique ? `: ${t.critique}` : ''}</div>;
              if (t.node === 'handoff') return <div key={i}>handoff · {t.reason}</div>;
              if (t.node?.startsWith('agent_')) return (
                <div key={i}>{agentLabel(t.node.slice(6))} · {t.tool ? `calls ${t.tool}` : t.finish ? 'done' : t.error ? `error: ${t.error}` : ''}{t.thought ? ` — ${t.thought}` : ''}</div>);
              return null;
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export function ApprovalCard({ approval, onDecide, decided }) {
  if (!approval) return null;
  if (approval.approver === 'staff') {
    return (
      <div className="flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
        <Clock size={13} /> Waiting for our team to approve: {approval.reason}
      </div>
    );
  }
  return (
    <div className="border border-zinc-200 rounded-2xl p-4 bg-white shadow-sm w-full max-w-[420px]">
      <div className="flex items-center gap-2 text-sm font-semibold text-zinc-800">
        <ShieldCheck size={16} className="text-zinc-700" /> Please confirm
      </div>
      <p className="text-sm text-zinc-600 mt-1">{approval.reason}</p>
      {decided ? (
        <p className="text-xs mt-3 text-zinc-500">{decided === 'yes' ? 'Confirmed' : 'Declined'}</p>
      ) : (
        <div className="flex gap-2 mt-3">
          <button onClick={() => onDecide(true)} className="px-4 py-2 rounded-xl bg-black text-white text-sm hover:opacity-90">Confirm</button>
          <button onClick={() => onDecide(false)} className="px-4 py-2 rounded-xl bg-zinc-100 text-zinc-700 text-sm hover:bg-zinc-200">Not now</button>
        </div>
      )}
    </div>
  );
}

export function UiCard({ ui }) {
  if (!ui || !ui.type || ui.type === 'products' || ui.type === 'approval') return null;
  if (ui.type === 'cart') {
    return (
      <div className="border border-zinc-200 rounded-2xl p-4 bg-white w-full max-w-[420px] text-sm">
        <div className="flex items-center gap-2 font-semibold mb-2"><Package size={15} /> Your cart</div>
        {(ui.items || []).length === 0 && <p className="text-zinc-500">Empty</p>}
        {(ui.items || []).map((i, k) => (
          <div key={k} className="flex justify-between py-1 border-b border-zinc-50 last:border-0">
            <span>{i.name} <span className="text-zinc-400">{[i.color, i.size].filter(Boolean).join(' · ')} × {i.quantity}</span></span>
            <span>₹{Math.round(i.line_total ?? 0)}</span>
          </div>
        ))}
        {ui.grand_total != null && <div className="flex justify-between font-semibold pt-2"><span>Total</span><span>₹{Math.round(ui.grand_total)}</span></div>}
      </div>
    );
  }
  if (ui.type === 'checkout') {
    return (
      <div className="border border-zinc-200 rounded-2xl p-4 bg-white w-full max-w-[420px] text-sm">
        <div className="font-semibold">Checkout ({ui.fulfillment || 'delivery'})</div>
        <div className="text-zinc-600 mt-1">Locked price ₹{Math.round(ui.locked_price || 0)}{ui.discount ? ` · discount ₹${Math.round(ui.discount)}` : ''}{ui.total ? ` · total ₹${Math.round(ui.total)}` : ''}</div>
        {ui.hold_minutes && <div className="text-xs text-zinc-400 mt-1">Stock held for {ui.hold_minutes} minutes</div>}
      </div>
    );
  }
  if (ui.type === 'order') {
    return (
      <div className="border border-zinc-200 rounded-2xl p-4 bg-white w-full max-w-[420px] text-sm">
        <div className="font-semibold">Order #{ui.ref || (ui.order_id || '').slice(0, 8)} · {ui.status}</div>
        {ui.total != null && <div className="text-zinc-600">₹{Math.round(ui.total)} · {ui.fulfillment}</div>}
        {(ui.items || []).map((i, k) => <div key={k} className="text-zinc-500 text-xs">{i.name} {[i.color, i.size].filter(Boolean).join(' · ')} × {i.qty}</div>)}
        {(ui.history || []).length > 0 && <div className="text-xs text-zinc-400 mt-2">Latest: {ui.history[ui.history.length - 1].status}</div>}
      </div>
    );
  }
  if (ui.type === 'orders') {
    return (
      <div className="border border-zinc-200 rounded-2xl p-3 bg-white w-full max-w-[420px] text-sm space-y-1">
        {(ui.orders || []).slice(0, 5).map((o, k) => (
          <div key={k} className="flex justify-between"><span>#{o.ref} · {o.status}</span><span>₹{Math.round(o.total)}</span></div>
        ))}
      </div>
    );
  }
  if (ui.type === 'offers') {
    const all = [...(ui.personalized || []).map(o => o.offer_name || o.name), ...(ui.system || []).map(c => `${c.code}${c.description ? ` — ${c.description}` : ''}`)];
    if (!all.length) return null;
    return (
      <div className="border border-zinc-200 rounded-2xl p-3 bg-white w-full max-w-[420px] text-sm space-y-1">
        {all.slice(0, 6).map((t, k) => <div key={k} className="flex items-center gap-2"><Tag size={12} />{t}</div>)}
      </div>
    );
  }
  return null;
}
