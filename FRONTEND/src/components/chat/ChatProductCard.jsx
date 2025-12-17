// src/components/chat/ChatProductCard.jsx
import React from 'react';
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from 'react-router-dom';

export default function ChatProductCard({ product }) {
  const navigate = useNavigate();

  return (
    <Card className="w-40 flex-shrink-0 bg-black/40 border border-white/10 overflow-hidden rounded-xl group cursor-pointer hover:border-cyan-500/50 transition-all">
      {/* Image Area */}
      <div className="aspect-[3/4] relative bg-white/5 overflow-hidden">
        {product.image_url ? (
          <img 
            src={product.image_url} 
            alt={product.name} 
            className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500" 
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-xs text-gray-500">No Image</div>
        )}
      </div>

      {/* Details */}
      <div className="p-2 space-y-1">
        <h4 className="text-xs font-medium text-white truncate" title={product.name}>
          {product.name}
        </h4>
        <div className="flex items-center justify-between">
            <p className="text-xs text-cyan-400 font-bold">₹{product.price || product.base_price || 0}</p>
            {product.inventory?.quantity < 5 && (
                <span className="text-[9px] text-red-400 font-medium">Low Stock</span>
            )}
        </div>
        
        <Button 
          size="sm" 
          variant="secondary" 
          className="w-full h-6 text-[10px] mt-1 bg-white/10 hover:bg-cyan-500 hover:text-black border-none"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/products/${product.id}`);
          }}
        >
          View Details
        </Button>
      </div>
    </Card>
  );
}