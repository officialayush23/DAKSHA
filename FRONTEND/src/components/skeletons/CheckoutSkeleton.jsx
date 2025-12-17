// FRONTEND/src/components/skeletons/CheckoutSkeleton.jsx

import { Skeleton } from "@/components/ui/skeleton";

export default function CheckoutSkeleton() {
  return (
    <div className="max-w-5xl mx-auto p-6 grid md:grid-cols-3 gap-8">
      
      <div className="md:col-span-2 space-y-4">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-24 rounded-xl" />
        <Skeleton className="h-24 rounded-xl" />
      </div>

      <div className="space-y-4">
        <Skeleton className="h-6 w-24" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-12 w-full rounded-xl" />
      </div>
    </div>
  );
}
