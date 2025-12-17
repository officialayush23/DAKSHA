//  src/modules/support_agent/pages/TicketList.jsx

import React, { useState, useEffect } from "react";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { 
  Search, Filter, CheckCircle, Clock, User, MessageSquare, MoreVertical, Loader2, AlertCircle, PlayCircle 
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Textarea } from "@/components/ui/textarea";

export default function TicketList() {
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState([]);
  
  // New Filter Logic: 'active' loads open/investigating
  const [viewMode, setViewMode] = useState("active"); 
  const [selectedTicket, setSelectedTicket] = useState(null);
  
  const [replyText, setReplyText] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // --- FETCH TICKETS ---
  const fetchTickets = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/support/tickets", {
        params: { status: viewMode } // 'active' or 'history'
      });
      setTickets(res.data || []);
      
      if (!selectedTicket && res.data && res.data.length > 0) {
        setSelectedTicket(res.data[0]);
      }
    } catch (error) {
      toast.error("Failed to load tickets.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
    setSelectedTicket(null);
  }, [viewMode]);

  // --- HANDLE STATUS CHANGE ---
  const updateStatus = async (newStatus) => {
    if (!selectedTicket) return;
    setActionLoading(true);
    try {
      await api.patch(`/admin/support/tickets/${selectedTicket.id}`, null, {
        params: {
          status: newStatus,
          resolution_notes: replyText || (newStatus === 'investigating' ? 'Investigation started' : 'Resolved via Dashboard')
        }
      });

      toast.success(`Ticket marked as ${newStatus}`);
      
      // If moving to a state not in current view, remove from list
      if (viewMode === 'active' && ['resolved_human', 'closed'].includes(newStatus)) {
         setTickets(prev => prev.filter(t => t.id !== selectedTicket.id));
         setSelectedTicket(null);
      } else {
         fetchTickets(); // Refresh
      }
      setReplyText("");

    } catch (error) {
      toast.error("Failed to update status.");
    } finally {
      setActionLoading(false);
    }
  };

  // Helper for Colors
  const getStatusColor = (status) => {
    switch(status) {
      case 'open': return 'bg-blue-600';
      case 'investigating': return 'bg-amber-600';
      case 'resolved_human': return 'bg-emerald-600';
      case 'resolved_bot': return 'bg-purple-600';
      case 'closed': return 'bg-zinc-600';
      default: return 'bg-zinc-600';
    }
  };

  return (
    <div className="flex h-[calc(100vh-100px)] gap-6 animate-in fade-in">
      
      {/* LEFT: LIST */}
      <div className="w-1/3 flex flex-col gap-4 bg-zinc-950/50 border border-zinc-800 rounded-xl overflow-hidden">
        
        {/* Toolbar */}
        <div className="p-4 border-b border-zinc-800 flex flex-col gap-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
            <Input placeholder="Search..." className="pl-9 bg-black border-zinc-800 h-9" />
          </div>
          <div className="flex bg-zinc-900 p-1 rounded-lg border border-zinc-800">
            <button 
              onClick={() => setViewMode("active")}
              className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-all ${viewMode === 'active' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              Inbox (Active)
            </button>
            <button 
              onClick={() => setViewMode("history")}
              className={`flex-1 text-xs font-medium py-1.5 rounded-md transition-all ${viewMode === 'history' ? 'bg-zinc-800 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}
            >
              Archived
            </button>
          </div>
        </div>

        {/* List Items */}
        <ScrollArea className="flex-1">
          {loading ? (
            <div className="flex justify-center p-8"><Loader2 className="animate-spin text-zinc-500"/></div>
          ) : tickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-8 text-zinc-500 text-sm h-full">
              <CheckCircle className="h-10 w-10 mb-2 opacity-20" />
              No {viewMode} tickets.
            </div>
          ) : (
            <div className="flex flex-col">
              {tickets.map(ticket => (
                <div 
                  key={ticket.id}
                  onClick={() => setSelectedTicket(ticket)}
                  className={`p-4 border-b border-zinc-800 cursor-pointer transition-colors hover:bg-zinc-900/50 ${selectedTicket?.id === ticket.id ? 'bg-zinc-900 border-l-2 border-l-indigo-500' : ''}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold text-sm text-white truncate max-w-[180px]">
                      {ticket.issue_summary || "No Subject"}
                    </span>
                    <Badge variant="secondary" className="text-[10px] h-5 bg-zinc-900 border-zinc-800 text-zinc-500">
                       {ticket.created_at.slice(0,10)}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-5 w-5">
                        <AvatarImage src={ticket.users?.avatar_url} />
                        <AvatarFallback className="text-[9px] bg-zinc-800 text-zinc-400">U</AvatarFallback>
                      </Avatar>
                      <span className="text-xs text-zinc-400 truncate max-w-[100px]">
                        {ticket.users?.full_name || "User"}
                      </span>
                    </div>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wide text-white ${getStatusColor(ticket.ticket_status)}`}>
                       {ticket.ticket_status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      {/* RIGHT: DETAIL */}
      <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden flex flex-col shadow-xl">
        {selectedTicket ? (
          <>
            <div className="p-6 border-b border-zinc-800 flex justify-between items-start bg-zinc-900/30">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">{selectedTicket.issue_summary}</h2>
                <div className="flex items-center gap-3">
                  <Badge className={`${getStatusColor(selectedTicket.ticket_status)} border-0`}>
                    {selectedTicket.ticket_status.replace('_', ' ')}
                  </Badge>
                  <span className="text-xs text-zinc-500 font-mono">ID: {selectedTicket.id.slice(0,8)}</span>
                </div>
              </div>
            </div>

            <ScrollArea className="flex-1 p-6">
              <div className="space-y-6">
                <div className="flex gap-4">
                  <Avatar className="h-10 w-10 border border-zinc-800">
                     <AvatarFallback className="bg-zinc-800">U</AvatarFallback>
                  </Avatar>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-white">{selectedTicket.users?.full_name}</p>
                    <div className="p-4 rounded-lg rounded-tl-none bg-zinc-900 text-zinc-300 text-sm border border-zinc-800">
                      {selectedTicket.conversation_summary || selectedTicket.issue_summary}
                    </div>
                  </div>
                </div>

                {selectedTicket.resolution_notes && (
                  <div className="flex gap-4 flex-row-reverse">
                    <Avatar className="h-10 w-10 border border-zinc-800">
                       <AvatarFallback className="bg-indigo-900 text-indigo-200">AI</AvatarFallback>
                    </Avatar>
                    <div className="space-y-1">
                       <p className="text-sm font-semibold text-white text-right">Agent Note</p>
                       <div className="p-4 rounded-lg rounded-tr-none bg-indigo-950/30 text-indigo-200 text-sm border border-indigo-900/50">
                         {selectedTicket.resolution_notes}
                       </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Actions (Only if Active) */}
            {['open', 'investigating'].includes(selectedTicket.ticket_status) && (
              <div className="p-4 border-t border-zinc-800 bg-zinc-900/30 space-y-4">
                <Textarea 
                  placeholder="Add resolution notes..." 
                  className="bg-black border-zinc-800 text-white min-h-[80px]"
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                />
                <div className="flex justify-end gap-3">
                  {selectedTicket.ticket_status === 'open' && (
                    <Button variant="outline" className="border-amber-900/50 text-amber-500 hover:bg-amber-950" onClick={() => updateStatus('investigating')} disabled={actionLoading}>
                       <PlayCircle className="h-4 w-4 mr-2" /> Start Investigation
                    </Button>
                  )}
                  <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => updateStatus('resolved_human')} disabled={actionLoading}>
                    {actionLoading ? <Loader2 className="animate-spin h-4 w-4"/> : <CheckCircle className="h-4 w-4 mr-2" />}
                    Resolve & Close
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-zinc-500">
            Select a ticket to view details
          </div>
        )}
      </div>

    </div>
  );
}