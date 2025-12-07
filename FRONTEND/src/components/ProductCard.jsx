import React from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingCart } from "lucide-react";
import { toast } from "sonner";
import { cartService } from "@/services/api";

const ProductCard = ({ product }) => {
  const handleAddToCart = async () => {
    try {
      const variantId = product.variants?.[0]?.id || product.default_variant_id;
      const storeId = product.store_id || "default_store"; 

      if (!variantId) {
        toast.error("Product unavailable");
        return;
      }

      await cartService.addToCart(variantId, storeId, 1);
      toast.success("Added to cart");
    } catch (error) {
      toast.error("Failed to add to cart");
    }
  };

  return (
    <Card className="w-full h-full flex flex-col hover:shadow-lg transition-shadow">
      <div className="relative pt-4 px-4 flex justify-center bg-secondary/10">
        <img 
          src={product.image_url || "https://placehold.co/300x300?text=No+Image"} 
          alt={product.name} 
          className="h-48 object-contain mix-blend-multiply"
        />
        {product.is_new && (
          <Badge className="absolute top-2 right-2">New</Badge>
        )}
      </div>

      <CardHeader>
        <CardTitle className="text-lg line-clamp-1" title={product.name}>
          {product.name}
        </CardTitle>
        <p className="text-sm text-muted-foreground line-clamp-2">
          {product.description}
        </p>
      </CardHeader>

      <CardContent className="mt-auto">
        <div className="flex justify-between items-center">
          <span className="text-xl font-bold">
            ${product.price?.toFixed(2) || "0.00"}
          </span>
          {product.style_tags && (
            <div className="flex gap-1">
              {product.style_tags.slice(0, 2).map(tag => (
                <span key={tag} className="text-xs bg-secondary px-2 py-1 rounded-md">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter>
        <Button onClick={handleAddToCart} className="w-full gap-2">
          <ShoppingCart className="w-4 h-4" /> Add to Cart
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ProductCard;