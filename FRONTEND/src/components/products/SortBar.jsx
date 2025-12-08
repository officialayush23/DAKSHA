import React from "react";
import { Select, SelectTrigger, SelectContent, SelectItem } from "@/components/ui/select";

export default function SortBar({ sort, setSort }) {
  return (
    <div className="flex justify-end">
      <Select value={sort} onValueChange={setSort}>
        <SelectTrigger className="w-48 border text-white bg-black border-white">
          Sort by
        </SelectTrigger>

        <SelectContent className="bg-black text-white">
          <SelectItem value="newest">Newest</SelectItem>
          <SelectItem value="price_low_high">Price: Low → High</SelectItem>
          <SelectItem value="price_high_low">Price: High → Low</SelectItem>
          <SelectItem value="popular">Most Popular</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
