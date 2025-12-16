// src/components/product/PDPSkeleton.jsx

import { Skeleton } from "@/components/ui/skeleton";

export default function PDPSkeleton() {
  return (
    <div className="max-w-6xl mx-auto p-6 grid md:grid-cols-2 gap-10">
      <Skeleton className="aspect-square rounded-xl" />
      <div className="space-y-4">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-3/4" />
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    </div>
  );
}
