import React from "react";
import { Edit, Trash2, Copy } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { TableCell, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export default function VariantRow({ variant, onEdit, onDelete }) {
  // Helper to copy SKU to clipboard
  const copySku = () => {
    navigator.clipboard.writeText(variant.sku);
    toast.success("SKU copied to clipboard");
  };

  return (
    <TableRow className="group hover:bg-muted/50 transition-colors">
      
      {/* 1. Image / Preview */}
      <TableCell className="py-2">
        <div className="h-10 w-10 rounded border bg-white dark:bg-slate-900 overflow-hidden flex items-center justify-center">
          {variant.image_url ? (
            <img 
              src={variant.image_url} 
              alt={variant.sku} 
              className="h-full w-full object-cover"
            />
          ) : (
            <div 
              className="h-full w-full"
              style={{ backgroundColor: variant.color_hex || "#e2e8f0" }} 
              title="Color Preview"
            />
          )}
        </div>
      </TableCell>

      {/* 2. SKU (Click to Copy) */}
      <TableCell className="font-mono text-xs font-medium">
        <div className="flex items-center gap-2">
          {variant.sku}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground"
                  onClick={copySku}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Copy SKU</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </TableCell>

      {/* 3. Specs */}
      <TableCell>
        <div className="flex flex-col text-sm">
          <span>{variant.color_name}</span>
          <span className="text-xs text-muted-foreground">Size: {variant.size_label}</span>
        </div>
      </TableCell>

      {/* 4. Price */}
      <TableCell>
        {variant.price_override ? (
          <div className="flex flex-col">
            <span className="font-semibold">₹{variant.price_override}</span>
            <span className="text-[10px] text-muted-foreground">Overridden</span>
          </div>
        ) : (
          <span className="text-muted-foreground text-xs italic">Use Base Price</span>
        )}
      </TableCell>

      {/* 5. Attributes (Quick View) */}
      <TableCell className="hidden md:table-cell">
        <div className="flex gap-1 flex-wrap max-w-[200px]">
          {variant.attributes && Object.entries(variant.attributes).map(([key, val], i) => (
            <Badge key={i} variant="secondary" className="text-[10px] px-1 py-0 h-5">
              {key}: {val}
            </Badge>
          ))}
        </div>
      </TableCell>

      {/* 6. Actions */}
      <TableCell className="text-right">
        <div className="flex justify-end gap-2">
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/20"
            onClick={() => onEdit(variant)}
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
            onClick={() => onDelete(variant.id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}