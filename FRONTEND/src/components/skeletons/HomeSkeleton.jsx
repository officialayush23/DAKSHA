// src/components/skeletons/HomeSkeleton.jsx
import { Skeleton } from "@/components/ui/skeleton";

export default function HomeSkeleton() {
  return (
    <div className="min-h-screen bg-background pb-20">
      
      {/* Header Skeleton */}
      <div className="sticky top-0 z-40 border-b border-white/5 bg-black/60 backdrop-blur-xl">
        <div className="h-20 max-w-7xl mx-auto flex items-center justify-between px-8">
          <div className="flex items-center gap-3">
             <Skeleton className="h-8 w-8 rounded-lg bg-white/10" />
             <Skeleton className="h-6 w-24 bg-white/10" />
          </div>
          <Skeleton className="h-10 w-96 rounded-full bg-white/5 hidden md:block" />
          <div className="flex gap-3">
            <Skeleton className="h-10 w-10 rounded-full bg-white/10" />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto">
        {/* Hero Skeleton */}
        <div className="px-4 md:px-8 mt-8">
            <Skeleton className="h-[400px] w-full rounded-[2.5rem] bg-white/5 border border-white/10" />
        </div>

        {/* Rail 1 */}
        <SectionSkeleton />
        {/* Rail 2 */}
        <SectionSkeleton />
      </div>
    </div>
  );
}

function SectionSkeleton() {
  return (
    <div className="px-4 md:px-8 mt-16">
      <div className="space-y-2 mb-6">
        <Skeleton className="h-8 w-48 bg-white/10" />
        <Skeleton className="h-4 w-32 bg-white/5" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-3">
             <Skeleton className="aspect-[4/5] rounded-2xl bg-white/5" />
             <div className="space-y-2 px-1">
                 <Skeleton className="h-4 w-3/4 bg-white/10" />
                 <Skeleton className="h-4 w-1/4 bg-white/10" />
             </div>
          </div>
        ))}
      </div>
    </div>
  );
}