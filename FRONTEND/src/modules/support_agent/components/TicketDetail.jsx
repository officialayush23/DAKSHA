//  src/modules/support_agent/components/TicketDetail.jsx

import React from "react";
import { 
  CheckCircle, Clock, User, MoreVertical, Loader2, MessageSquare, AlertCircle 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Textarea } from "@/components/ui/textarea";

export default function TicketDetail({ 
  ticket, 
  replyText, 
  setReplyText, 
  onResolve, 
  resolving 
}) {
  if (!ticket) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-500">
        <MessageSquare className="h-16 w-16 mb-6 opacity-10" />
        <p className="text-lg font-medium text-zinc-400">No Ticket Selected</p>
        <p className="text-sm max-w-xs text-center mt-2">Select a ticket from the list on the left to view details and take action.</p>
      </div>
    );
  }

  return (
    <>
      {/* Detail Header */}
      <div className="p-6 border-b border-zinc-800 flex justify-between items-start bg-zinc-900/30">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-xl font-bold text-white">{ticket.issue_summary || "Support Request"}</h2>
            <Badge className={`capitalize ${ticket.ticket_status === 'open' ? 'bg-indigo-600' : 'bg-emerald-600'}`}>
              {ticket.ticket_status}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-sm text-zinc-400">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4" />
              {ticket.users?.full_name || "Unknown User"}
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              {new Date(ticket.created_at).toLocaleString()}
            </div>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-white">
          <MoreVertical className="h-5 w-5" />
        </Button>
      </div>

      {/* Conversation Area */}
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6">
          
          {/* User's Issue */}
          <div className="flex gap-4">
            <Avatar className="h-10 w-10 border border-zinc-800">
              <AvatarImage src={ticket.users?.avatar_url} />
              <AvatarFallback className="bg-zinc-900 text-zinc-400">
                {ticket.users?.full_name?.[0]}
              </AvatarFallback>
            </Avatar>
            <div className="space-y-1 max-w-[85%]">
              <div className="flex items-baseline gap-2">
                <span className="font-semibold text-white">{ticket.users?.full_name}</span>
                <span className="text-xs text-zinc-500">Customer</span>
              </div>
              <div className="p-4 rounded-lg rounded-tl-none bg-zinc-900 text-zinc-300 text-sm leading-relaxed border border-zinc-800">
                {ticket.conversation_summary || ticket.issue_summary || "No description provided."}
              </div>
            </div>
          </div>

          {/* System/Agent Notes (if any) */}
          {(ticket.resolution_notes || ticket.resolved_by) && (
            <div className="flex gap-4 flex-row-reverse">
              <Avatar className="h-10 w-10 border border-zinc-800">
                <AvatarFallback className="bg-indigo-900 text-indigo-200">AG</AvatarFallback>
              </Avatar>
              <div className="space-y-1 max-w-[85%]">
                <div className="flex items-baseline gap-2 justify-end">
                  <span className="font-semibold text-white">Support Agent</span>
                  <span className="text-xs text-zinc-500">Resolution Note</span>
                </div>
                <div className="p-4 rounded-lg rounded-tr-none bg-indigo-950/30 text-indigo-200 text-sm leading-relaxed border border-indigo-900/50">
                  {ticket.resolution_notes || "Ticket marked resolved."}
                </div>
              </div>
            </div>
          )}
          
          {ticket.ticket_status === 'open' && (
              <div className="flex justify-center">
                  <span className="text-xs text-zinc-600 flex items-center gap-1 bg-zinc-900/50 px-3 py-1 rounded-full">
                      <AlertCircle className="h-3 w-3" /> Ticket is currently active
                  </span>
              </div>
          )}

        </div>
      </ScrollArea>

      {/* Action Footer */}
      {ticket.ticket_status === 'open' && (
        <div className="p-4 border-t border-zinc-800 bg-zinc-900/30 space-y-4">
          <Textarea 
            placeholder="Type resolution notes (internal or visible to user)..." 
            className="bg-black border-zinc-800 text-white resize-none min-h-[80px] focus-visible:ring-indigo-500 focus-visible:border-indigo-500"
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
          />
          <div className="flex justify-between items-center">
            <div className="text-xs text-zinc-500 font-mono">
              ID: {ticket.id.slice(0,8)}...
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" className="text-zinc-400 hover:text-white hover:bg-zinc-800">
                Cancel
              </Button>
              <Button 
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-900/20" 
                onClick={onResolve}
                disabled={resolving}
              >
                {resolving ? <Loader2 className="animate-spin h-4 w-4 mr-2"/> : <CheckCircle className="h-4 w-4 mr-2" />}
                Resolve Ticket
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}