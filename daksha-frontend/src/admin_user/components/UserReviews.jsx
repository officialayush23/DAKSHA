import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Star, MessageSquare, Calendar, 
  Package, ArrowRight, Quote 
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from 'sonner';
import { Link } from 'react-router-dom';

// --- Helper: Render Star Rating ---
const StarRating = ({ rating }) => {
  const maxStars = 5;
  const validRating = Math.max(0, Math.min(Number(rating) || 0, maxStars));

  return (
    <div className="flex items-center gap-1">
      {[...Array(maxStars)].map((_, i) => (
        <Star 
          key={i} 
          size={16} 
          className={i < validRating ? "fill-amber-400 text-amber-400" : "fill-zinc-100 text-zinc-200"} 
        />
      ))}
      <span className="ml-2 text-xs font-bold text-zinc-700">{validRating}.0</span>
    </div>
  );
};

export default function UserReviews({ userId }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReviews = async () => {
      try {
        setLoading(true);
        const res = await AdminUserService.getUserReviews(userId);
        const fetchedReviews = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
        
        // Sort by newest first
        setReviews(fetchedReviews.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)));
      } catch (error) {
        console.error("Failed to load user reviews", error);
        toast.error("Could not load the user's review history.");
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchReviews();
  }, [userId]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-48 w-full rounded-[2.5rem] bg-zinc-50" />
        ))}
      </div>
    );
  }

  if (reviews.length === 0) {
    return (
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] min-h-[400px] flex flex-col items-center justify-center text-center p-10">
        <div className="w-20 h-20 bg-amber-50 rounded-full flex items-center justify-center mb-6 border border-amber-100">
          <MessageSquare size={32} className="text-amber-500" strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-serif font-bold text-zinc-900 mb-2">No Reviews Yet</h3>
        <p className="text-zinc-500 max-w-sm">This customer hasn't left any product reviews or ratings.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <AnimatePresence>
        {reviews.map((review, index) => {
          const reviewId = review.id || "Unknown";
          const displayId = reviewId.toString().slice(-8).toUpperCase();
          const productId = review.product_id || "Unknown Product";
          const productDisplayId = productId.toString().slice(-8).toUpperCase();
          const date = review.created_at 
            ? new Date(review.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) 
            : 'Unknown Date';

          return (
            <motion.div
              key={reviewId}
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              className="group bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] p-8 hover:shadow-xl hover:border-zinc-200 transition-all duration-300 flex flex-col relative overflow-hidden"
            >
              {/* Decorative Quote Icon Background */}
              <Quote size={120} className="absolute -top-6 -right-6 text-zinc-50/50 -rotate-12 pointer-events-none" />

              <div className="relative z-10 flex flex-col h-full">
                
                {/* Header: Rating & Date */}
                <div className="flex items-start justify-between mb-6 gap-4">
                  <div>
                    <StarRating rating={review.rating} />
                    <span className="text-[10px] font-mono font-bold text-zinc-400 mt-2 block">
                      ID: #{displayId}
                    </span>
                  </div>
                  <div className="text-xs font-medium text-zinc-400 flex items-center gap-1.5 shrink-0 bg-zinc-50 px-3 py-1.5 rounded-full border border-zinc-100">
                    <Calendar size={12} /> {date}
                  </div>
                </div>

                {/* Body: Review Comment */}
                <div className="flex-1 mb-8">
                  <p className="text-base md:text-lg font-medium text-zinc-700 leading-relaxed italic">
                    "{review.comment || review.content || "User left a rating without a comment."}"
                  </p>
                </div>

                {/* Footer: Product Reference */}
                <div className="pt-5 border-t border-zinc-50 flex items-center justify-between mt-auto">
                  <div className="flex flex-col">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1 flex items-center gap-1.5">
                      <Package size={12} /> Reviewed Item
                    </p>
                    <p className="text-xs font-mono font-bold text-zinc-900">
                      Product #{productDisplayId}
                    </p>
                  </div>
                  
                  {/* Quick link to the product in the admin catalog */}
                  <Link 
                    to={`/admin/products/${productId}`}
                    className="w-10 h-10 rounded-full bg-zinc-50 flex items-center justify-center text-zinc-400 hover:bg-zinc-900 hover:text-white hover:shadow-md transition-all duration-300 shrink-0"
                    title="View Product"
                  >
                    <ArrowRight size={16} className="-rotate-45" />
                  </Link>
                </div>

              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}