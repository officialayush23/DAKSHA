// src/modules/store_manager/components/InventoryCard.jsx

import React from "react";
import { 
  MapPin, 
  AlertTriangle, 
  Package, 
  Edit2,
  Box
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export default function InventoryCard({ item, onAdjust }) {
  // Safe Accessors
  const variant = item?.product_variants || {};
  const product = variant?.products || {};
  
  const currentQty = item.quantity_on_hand || 0;
  const threshold = item.low_stock_threshold || 10;
  
  // Logic: Determine Status
  const isCritical = currentQty === 0;
  const isLow = currentQty <= threshold;
  
  // Logic: Color Theme based on status
  const statusColor = isCritical 
    ? "border-red-900/50 bg-red-950/10 hover:border-red-800" 
    : isLow 
      ? "border-amber-900/50 bg-amber-950/10 hover:border-amber-800" 
      : "border-zinc-800 bg-zinc-950 hover:border-zinc-700";

  const textColor = isCritical 
    ? "text-red-500" 
    : isLow 
      ? "text-amber-500" 
      : "text-emerald-500";

  // Calculate percentage for progress bar (capped at 100)
  const healthPercent = Math.min((currentQty / (threshold * 3)) * 100, 100);

  return (
    <div className={`group relative flex items-center gap-4 p-4 rounded-xl border transition-all duration-300 ${statusColor}`}>
      
      {/* 1. IMAGE THUMBNAIL */}
      <div className="relative h-16 w-16 shrink-0 rounded-lg bg-black border border-zinc-800 overflow-hidden flex items-center justify-center">
        {variant.image_url ? (
          <img src={variant.image_url} alt={product.name} className="h-full w-full object-cover" />
        ) : (
          <Box className="h-6 w-6 text-zinc-700" />
        )}
        {isLow && (
          <div className="absolute top-0 right-0 p-1 bg-black/50 backdrop-blur">
            <AlertTriangle className={`h-3 w-3 ${isCritical ? 'text-red-500' : 'text-amber-500'}`} />
          </div>
        )}
      </div>

      {/* 2. PRODUCT DETAILS */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="text-sm font-bold text-zinc-100 truncate leading-none">
            {product.name || "Unknown Product"}
          </h4>
          <Badge variant="outline" className="border-zinc-800 text-[10px] text-zinc-500 px-1.5 py-0 h-4 font-mono">
            {variant.sku}
          </Badge>
        </div>
        
        <p className="text-xs text-zinc-500 truncate mb-2">
          {variant.color_name} • {variant.size_label}
        </p>

        {/* Location Tag */}
        <div className="flex items-center gap-1.5 text-[10px] text-zinc-400 bg-black/40 w-fit px-2 py-1 rounded border border-zinc-800/50">
          <MapPin className="h-3 w-3 text-zinc-500" />
          <span>Aisle <span className="text-white font-medium">{item.aisle_number || "-"}</span></span>
          <span className="text-zinc-700">|</span>
          <span>Shelf <span className="text-white font-medium">{item.shelf_height || "-"}</span></span>
        </div>
      </div>

      {/* 3. STOCK LEVEL & ACTION */}
      <div className="flex flex-col items-end gap-1 min-w-[80px]">
        <div className="text-right">
          <span className={`text-xl font-bold font-mono tracking-tight ${textColor}`}>
            {currentQty}
          </span>
          <span className="text-[10px] text-zinc-600 ml-1 uppercase">Units</span>
        </div>
        
        {/* Visual Health Bar */}
        <div className="w-full h-1 bg-zinc-900 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full ${isCritical ? 'bg-red-600' : isLow ? 'bg-amber-600' : 'bg-emerald-600'}`} 
            style={{ width: `${healthPercent}%` }}
          />
        </div>

        {/* Adjust Button (Hidden until hover) */}
        <Button 
          onClick={() => onAdjust(item)}
          variant="ghost" 
          size="sm" 
          className="mt-2 h-7 px-2 text-[10px] text-zinc-500 hover:text-white hover:bg-zinc-800 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Edit2 className="mr-1.5 h-3 w-3" /> Adjust
        </Button>
      </div>

    </div>
  );
}