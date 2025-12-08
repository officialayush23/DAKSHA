import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Filters({ setCategory, setBrand }) {
  const categories = ["Men", "Women", "Kids", "Shoes", "Accessories"];
  const brands = ["Nike", "Adidas", "Puma", "HRX", "Reebok"];

  return (
    <Card className="p-4 border bg-black text-white rounded-xl">
      <CardHeader className="p-0 mb-3">
        <CardTitle className="text-xl">Filters</CardTitle>
      </CardHeader>

      <CardContent className="space-y-6 p-0">
        {/* Category */}
        <div>
          <p className="mb-2 font-medium">Category</p>
          <div className="flex flex-col gap-2">
            {categories.map((c) => (
              <Button
                key={c}
                variant="outline"
                className="border-white text-white"
                onClick={() => setCategory(c)}
              >
                {c}
              </Button>
            ))}
          </div>
        </div>

        {/* Brand */}
        <div>
          <p className="mb-2 font-medium">Brand</p>
          <div className="flex flex-col gap-2">
            {brands.map((b) => (
              <Button
                key={b}
                variant="outline"
                className="border-white text-white"
                onClick={() => setBrand(b)}
              >
                {b}
              </Button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
