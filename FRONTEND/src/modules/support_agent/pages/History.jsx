import React, { useState, useEffect } from "react";
import api from "@/lib/apiClient";
import { CheckCircle, Search, Calendar, User, Loader2, Archive, XCircle, Bot } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function History() {
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        // Fetch ALL history (resolved_human, resolved_bot, closed)
        const res = await api.get("/admin/support/tickets", {
          params: { status: "history" } 
        });
        setTickets(res.data || []);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const filtered = tickets.filter(t => JSON.stringify(t).toLowerCase().includes(search.toLowerCase()));

  const getStatusBadge = (status) => {
    switch(status) {
        case 'resolved_human': return <Badge className="bg-emerald-600 hover:bg-emerald-700"><CheckCircle className="h-3 w-3 mr-1"/> Resolved (Agent)</Badge>;
        case 'resolved_bot': return <Badge className="bg-purple-600 hover:bg-purple-700"><Bot className="h-3 w-3 mr-1"/> Auto-Resolved</Badge>;
        case 'closed': return <Badge className="bg-zinc-600 hover:bg-zinc-700"><XCircle className="h-3 w-3 mr-1"/> Closed</Badge>;
        default: return <Badge variant="outline">{status}</Badge>;
    }
  }

  return (
    <div className="w-full space-y-6 animate-in fade-in">
      <div className="flex justify-between items-end gap-4 border-b border-zinc-900 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white flex items-center gap-2"><Archive className="h-8 w-8 text-zinc-500" /> Resolution Archive</h2>
          <p className="text-zinc-400 text-sm">Audit past tickets.</p>
        </div>
        <div className="relative w-72">
           <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
           <Input placeholder="Search history..." className="pl-9 bg-zinc-950 border-zinc-800" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>

      <Card className="bg-zinc-950 border-zinc-800 overflow-hidden">
        <Table>
            <TableHeader className="bg-zinc-900/50">
              <TableRow className="border-zinc-800">
                <TableHead className="text-zinc-500">ID</TableHead>
                <TableHead className="text-zinc-500">Status</TableHead>
                <TableHead className="text-zinc-500">Issue</TableHead>
                <TableHead className="text-zinc-500">Customer</TableHead>
                <TableHead className="text-zinc-500 text-right">Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={5} className="text-center h-32"><Loader2 className="h-6 w-6 animate-spin mx-auto"/></TableCell></TableRow>
              ) : filtered.length === 0 ? (
                <TableRow><TableCell colSpan={5} className="text-center h-32 text-zinc-500">No records found.</TableCell></TableRow>
              ) : (
                filtered.map(t => (
                  <TableRow key={t.id} className="border-zinc-800 hover:bg-zinc-900/30">
                    <TableCell className="font-mono text-xs text-zinc-500">{t.id.slice(0,8)}</TableCell>
                    <TableCell>{getStatusBadge(t.ticket_status)}</TableCell>
                    <TableCell className="text-zinc-300 text-sm">{t.issue_summary}</TableCell>
                    <TableCell className="text-zinc-400 text-sm">{t.users?.full_name}</TableCell>
                    <TableCell className="text-right text-zinc-500 text-xs">{new Date(t.updated_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
        </Table>
      </Card>
    </div>
  );
}