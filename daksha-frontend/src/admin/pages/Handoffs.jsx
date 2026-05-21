// src/admin/pages/Handoffs.jsx — Live WebSocket human handoff panel
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  MessageSquare, User, Clock, CheckCircle,
  RefreshCw, Send, Loader2, Wifi, WifiOff
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { toast } from "sonner";

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE  = API_BASE.replace(/^http/, 'ws');

function statusColor(s) {
  return s === 'open'        ? 'bg-red-500/15 text-red-400 border-red-500/30'
       : s === 'in_progress' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
       : s === 'resolved'    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
       : 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30';
}

function Bubble({ msg }) {
  const isAdmin  = msg.speaker === 'admin';
  const isSystem = msg.speaker === 'system';
  if (isSystem) return (
    <div className="flex justify-center mb-2">
      <span className="text-xs text-zinc-500 italic px-3 py-1 bg-zinc-800/60 rounded-full">{msg.message}</span>
    </div>
  );
  return (
    <div className={`flex ${isAdmin ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${isAdmin ? 'bg-violet-600 text-white rounded-br-sm' : 'bg-zinc-800 text-zinc-100 rounded-bl-sm'}`}>
        <p>{msg.message}</p>
        <p className={`text-[10px] mt-1 ${isAdmin ? 'text-violet-300' : 'text-zinc-500'}`}>
          {isAdmin ? 'You' : 'Customer'} · {msg.created_at ? format(new Date(msg.created_at), 'HH:mm') : ''}
        </p>
      </div>
    </div>
  );
}

export default function Handoffs() {
  const [handoffs, setHandoffs]             = useState([]);
  const [loading, setLoading]               = useState(true);
  const [selected, setSelected]             = useState(null);
  const [messages, setMessages]             = useState([]);
  const [replyText, setReplyText]           = useState('');
  const [wsStatus, setWsStatus]             = useState('disconnected');
  const [resolving, setResolving]           = useState(false);
  const wsRef        = useRef(null);
  const bottomRef    = useRef(null);
  const adminId      = localStorage.getItem('admin_id') || 'admin';

  const fetchHandoffs = useCallback(async () => {
    setLoading(true);
    try {
      const res  = await fetch(`${API_BASE}/ws/admin/handoffs/open`, { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
      const data = await res.json();
      setHandoffs(Array.isArray(data) ? data : []);
    } catch { toast.error('Could not load handoffs'); }
    finally  { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchHandoffs();
    const t = setInterval(fetchHandoffs, 15000);
    return () => clearInterval(t);
  }, [fetchHandoffs]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const openHandoff = useCallback((h) => {
    wsRef.current?.close();
    setSelected(h); setMessages([]); setWsStatus('connecting');
    const ws = new WebSocket(`${WS_BASE}/ws/admin/${h.id}`);
    wsRef.current = ws;
    ws.onopen = () => setWsStatus('connected');
    ws.onmessage = (e) => {
      const d = JSON.parse(e.data);
      if (d.type === 'history')           setMessages(d.messages || []);
      else if (d.type === 'message')      setMessages(p => [...p, { id: Date.now(), speaker: d.speaker, message: d.message, created_at: d.timestamp }]);
      else if (d.type === 'handoff_resolved') { toast.success('Resolved — AI resumed'); fetchHandoffs(); setSelected(null); setMessages([]); }
      else if (d.type === 'assigned')     toast.info('Assigned to you');
    };
    ws.onclose = () => setWsStatus('disconnected');
    ws.onerror = () => { setWsStatus('disconnected'); toast.error('Connection lost'); };
  }, [fetchHandoffs]);

  useEffect(() => () => wsRef.current?.close(), []);

  const send = () => {
    if (!replyText.trim() || wsRef.current?.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type: 'message', message: replyText.trim(), admin_id: adminId }));
    setReplyText('');
  };

  const resolve = () => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;
    setResolving(true);
    wsRef.current.send(JSON.stringify({ type: 'resolve', admin_id: adminId, note: 'Resolved by admin' }));
    setResolving(false);
  };

  const wsIcon = wsStatus === 'connected' ? <Wifi className="h-3 w-3"/> : wsStatus === 'connecting' ? <Loader2 className="h-3 w-3 animate-spin"/> : <WifiOff className="h-3 w-3"/>;
  const wsColor = wsStatus === 'connected' ? 'text-emerald-400' : wsStatus === 'connecting' ? 'text-amber-400' : 'text-zinc-500';

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-4 p-4">
      {/* LEFT: handoff list */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-100">Live Handoffs</h2>
          <Button variant="ghost" size="icon" onClick={fetchHandoffs}><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`}/></Button>
        </div>
        <ScrollArea className="flex-1">
          {loading && !handoffs.length ? (
            <div className="flex items-center justify-center h-32"><Loader2 className="h-5 w-5 animate-spin text-zinc-500"/></div>
          ) : !handoffs.length ? (
            <div className="text-center py-12 text-zinc-500"><CheckCircle className="h-8 w-8 mx-auto mb-2 opacity-40"/><p className="text-sm">No open handoffs</p></div>
          ) : handoffs.map(h => (
            <Card key={h.id} onClick={() => openHandoff(h)} className={`mb-2 cursor-pointer transition-all border ${selected?.id === h.id ? 'border-violet-500/60 bg-violet-950/20' : 'border-zinc-800 hover:border-zinc-600 bg-zinc-900/50'}`}>
              <CardContent className="p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <User className="h-4 w-4 text-zinc-400 flex-shrink-0"/>
                    <span className="text-xs font-medium text-zinc-200 truncate">{h.user_id?.slice(0,8) || 'Guest'}</span>
                  </div>
                  <Badge className={`text-[10px] px-1.5 py-0 border ${statusColor(h.status)}`}>{h.status}</Badge>
                </div>
                <p className="text-xs text-zinc-400 mt-1.5 line-clamp-2">{h.reason || 'No reason provided'}</p>
                <div className="flex items-center gap-1 mt-2 text-[10px] text-zinc-600">
                  <Clock className="h-3 w-3"/>
                  {h.created_at ? formatDistanceToNow(new Date(h.created_at), { addSuffix: true }) : '—'}
                </div>
                {h.from_agent_name && <Badge variant="outline" className="mt-1 text-[9px] px-1 py-0 text-zinc-500 border-zinc-700">from {h.from_agent_name}</Badge>}
              </CardContent>
            </Card>
          ))}
        </ScrollArea>
      </div>

      {/* RIGHT: chat panel */}
      <div className="flex-1 flex flex-col rounded-xl border border-zinc-800 bg-zinc-900/40 overflow-hidden">
        {selected ? (
          <>
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900/80">
              <div className="flex items-center gap-3">
                <MessageSquare className="h-4 w-4 text-violet-400"/>
                <div>
                  <p className="text-sm font-medium text-zinc-100">Customer {selected.user_id?.slice(0,8) || 'Guest'}</p>
                  <p className="text-xs text-zinc-500">{selected.reason || 'Escalated by agent'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className={`flex items-center gap-1 text-xs ${wsColor}`}>{wsIcon}<span className="capitalize">{wsStatus}</span></div>
                <Separator orientation="vertical" className="h-5 bg-zinc-700"/>
                <Button size="sm" variant="outline" className="text-xs border-zinc-700 hover:bg-zinc-800" onClick={() => wsRef.current?.send(JSON.stringify({ type: 'assign', admin_id: adminId }))} disabled={wsStatus !== 'connected'}>Assign to me</Button>
                <Button size="sm" className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white" onClick={resolve} disabled={wsStatus !== 'connected' || resolving}>
                  {resolving ? <Loader2 className="h-3 w-3 animate-spin mr-1"/> : <CheckCircle className="h-3 w-3 mr-1"/>} Resolve
                </Button>
              </div>
            </div>
            {selected.summary && <div className="px-4 py-2 bg-amber-950/20 border-b border-amber-900/30 text-xs text-amber-300"><span className="font-medium">AI Summary:</span> {selected.summary}</div>}

            {/* Messages */}
            <ScrollArea className="flex-1 px-4 py-3">
              {messages.length === 0
                ? <div className="flex items-center justify-center h-full text-zinc-600 text-sm">{wsStatus === 'connecting' ? 'Loading history…' : 'No messages yet.'}</div>
                : messages.map((m, i) => <Bubble key={m.id || i} msg={m}/>)
              }
              <div ref={bottomRef}/>
            </ScrollArea>

            {/* Input */}
            <div className="px-4 py-3 border-t border-zinc-800 flex gap-2">
              <Textarea
                value={replyText}
                onChange={e => setReplyText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
                placeholder="Reply… (Enter to send)"
                className="flex-1 min-h-[40px] max-h-[120px] resize-none bg-zinc-800 border-zinc-700 text-zinc-100 text-sm placeholder:text-zinc-600"
                disabled={wsStatus !== 'connected'}
              />
              <Button onClick={send} disabled={!replyText.trim() || wsStatus !== 'connected'} className="bg-violet-600 hover:bg-violet-700 self-end" size="icon">
                <Send className="h-4 w-4"/>
              </Button>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-zinc-600 gap-3">
            <MessageSquare className="h-12 w-12 opacity-20"/>
            <p className="text-sm">Select a handoff to start the live chat</p>
          </div>
        )}
      </div>
    </div>
  );
}
