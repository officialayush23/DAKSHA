import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingBag, ArrowRight } from 'lucide-react';

export default function ProductCardLarge({ product }) {
  const navigate = useNavigate();

  // Handle tap
  const handleClick = () => {
    navigate(`/kiosk/product/${product.id}`);
  };

  // Format price
  const price = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(product.base_price || product.price || 0);

  return (
    <Card 
      className="overflow-hidden cursor-pointer h-full flex flex-col hover:shadow-xl transition-all duration-300 active:scale-95 border-2 hover:border-primary/20"
      onClick={handleClick}
    >
      {/* Image Container */}
      <div className="relative aspect-[3/4] bg-slate-100 overflow-hidden">
        {product.images && product.images.length > 0 ? (
          <img 
            src={product.images[0].image_url || product.images[0]} 
            alt={product.name || product.brand}
            className="w-full h-full object-cover transition-transform duration-500 hover:scale-110"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-300">
            <ShoppingBag className="w-16 h-16" />
          </div>
        )}
        
        {/* New / Sale Badges could go here */}
        {product.is_new && (
          <Badge className="absolute top-4 left-4 bg-blue-600 text-white px-3 py-1 text-sm">
            New Arrival
          </Badge>
        )}
      </div>

      {/* Content */}
      <CardContent className="p-6 flex-1 flex flex-col gap-2">
        <div className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          {product.brand}
        </div>
        <h3 className="text-xl font-bold text-slate-900 leading-tight line-clamp-2">
          {product.name || `${product.brand} ${product.category}`}
        </h3>
      </CardContent>

      {/* Footer */}
      <CardFooter className="p-6 pt-0 flex items-center justify-between mt-auto">
        <div className="text-2xl font-bold text-primary">
          {price}
        </div>
        <Button size="icon" className="rounded-full w-12 h-12 shrink-0">
          <ArrowRight className="w-6 h-6" />
        </Button>
      </CardFooter>
    </Card>
  );
}