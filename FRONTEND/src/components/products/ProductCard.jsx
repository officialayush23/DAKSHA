import React from "react";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ProductCard({ product }) {
  return (
    <Card className="border bg-black text-white hover:bg-neutral-900 transition rounded-xl">
      <CardContent className="p-0">
        <img
          src={product.thumbnail}
          alt={product.name}
          className="w-full h-48 object-cover rounded-t-xl"
        />
      </CardContent>

      <CardFooter className="p-3 flex flex-col gap-1">
        <div className="font-semibold">{product.name}</div>
        <div className="text-sm text-neutral-400">{product.brand}</div>
        <div className="mt-2 font-bold text-lg">₹{product.price}</div>

        <Button variant="outline" className="mt-3 w-full text-white border-white">
          View Details
        </Button>
      </CardFooter>
    </Card>
  );
}
