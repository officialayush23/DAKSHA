import React from "react";
import { format } from "date-fns";
import { 
  Box, 
  User, 
  Clock, 
  MoreHorizontal, 
  Truck
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function OrderRow({ order, onProcess }) {
  const user = order.users || {};
  const itemCount = order.order_items?.length || 0;
  
  // Logic: Status Colors
  const getStatusColor = (status) => {
    switch(status) {
      case 'pending': return "bg-amber-950/30 text-amber-500 border-amber-900/50";
      case 'processing': return "bg-blue-950/30 text-blue-400 border-blue-900/50";
      case 'ready_for_pickup': return "bg-emerald-950/30 text-emerald-400 border-emerald-900/50";
      case 'shipped': return "bg-zinc-800 text-zinc-400 border-zinc-700";
      default: return "bg-zinc-900 text-zinc-500 border-zinc-800";
    }
  };

  return (
    <div className="group flex items-center justify-between p-3 rounded-lg border border-transparent hover:bg-zinc-900/50 hover:border-zinc-800 transition-all duration-200">
      
      {/* 1. ORDER ID & TIME */}
      <div className="flex flex-col w-32 shrink-0">
        <span className="font-mono text-sm font-medium text-white">
          #{order.id.slice(0, 8).toUpperCase()}
        </span>
        <div className="flex items-center gap-1.5 mt-1 text-xs text-zinc-500">
          <Clock className="h-3 w-3" />
          {/* Safety Check for date */}
          <span>{order.created_at ? format(new Date(order.created_at), "h:mm a") : "--"}</span>
        </div>
      </div>

      {/* 2. CUSTOMER INFO */}
      <div className="flex-1 min-w-[150px] px-4">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-full bg-zinc-800 flex items-center justify-center">
            <User className="h-3 w-3 text-zinc-400" />
          </div>
          <span className="text-sm text-zinc-300 truncate font-medium">
            {user.full_name || "Guest Customer"}
          </span>
        </div>
        <p className="text-xs text-zinc-500 pl-8 mt-0.5">
          {itemCount} item{itemCount !== 1 ? 's' : ''} • ₹{order.total_amount}
        </p>
      </div>

      {/* 3. STATUS BADGE */}
      <div className="w-32 flex justify-center">
        <Badge variant="outline" className={`h-6 px-2 text-[10px] uppercase tracking-wide border ${getStatusColor(order.status)}`}>
          {order.status?.replace(/_/g, " ") || "UNKNOWN"}
        </Badge>
      </div>

      {/* 4. ACTIONS (Primary Action appears on Hover) */}
      <div className="flex items-center justify-end gap-2 w-32 pl-4">
        
        {/* Context-Aware Primary Button */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          {order.status === 'pending' && (
            <Button size="sm" variant="secondary" onClick={() => onProcess(order)} className="h-7 text-xs bg-white text-black hover:bg-zinc-200">
              Pack
            </Button>
          )}
          {order.status === 'processing' && (
            <Button size="sm" variant="secondary" onClick={() => onProcess(order)} className="h-7 text-xs bg-emerald-600 text-white hover:bg-emerald-700">
              Ready
            </Button>
          )}
        </div>

        {/* Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-7 w-7 text-zinc-500 hover:text-white">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-zinc-950 border-zinc-800 text-white">
            <DropdownMenuItem className="focus:bg-zinc-900 cursor-pointer text-xs">
              <Box className="mr-2 h-3 w-3" /> View Items
            </DropdownMenuItem>
            <DropdownMenuItem className="focus:bg-zinc-900 cursor-pointer text-xs">
              <Truck className="mr-2 h-3 w-3" /> Track Shipment
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

      </div>
    </div>
  );
}