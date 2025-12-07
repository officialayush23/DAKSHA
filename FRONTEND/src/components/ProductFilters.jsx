import React from 'react';
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";

const ProductFilters = ({ activeFilters, onFilterChange }) => {
  const categories = ["Electronics", "Clothing", "Home", "Beauty"];
  const priceRanges = ["Under $50", "$50 - $100", "$100 - $200", "$200+"];

  const handleCategoryChange = (category) => {
    const current = activeFilters.categories || [];
    const newCategories = current.includes(category)
      ? current.filter(c => c !== category)
      : [...current, category];
    
    onFilterChange({ ...activeFilters, categories: newCategories });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-semibold mb-4">Categories</h3>
        <div className="space-y-3">
          {categories.map((cat) => (
            <div key={cat} className="flex items-center space-x-2">
              <Checkbox 
                id={cat} 
                checked={activeFilters.categories?.includes(cat)}
                onCheckedChange={() => handleCategoryChange(cat)}
              />
              <Label htmlFor={cat} className="text-sm font-normal cursor-pointer">
                {cat}
              </Label>
            </div>
          ))}
        </div>
      </div>
      
      <Separator />

      <div>
        <h3 className="font-semibold mb-4">Price Range</h3>
        <div className="space-y-3">
          {priceRanges.map((range) => (
            <div key={range} className="flex items-center space-x-2">
              <Checkbox id={range} />
              <Label htmlFor={range} className="text-sm font-normal cursor-pointer">
                {range}
              </Label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProductFilters;