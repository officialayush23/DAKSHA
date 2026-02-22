import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Ticket, Scissors, History, CheckCircle2, 
  Percent, AlertCircle, Calendar, ShoppingBag
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

export default function UserCoupons({ userId }) {
  const [offers, setOffers] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCouponsData = async () => {
      try {
        setLoading(true);
        // Fetch both personalized offers and redemption history simultaneously
        const [offersRes, redemptionsRes] = await Promise.all([
          AdminUserService.getUserPersonalizedCoupons(userId).catch(() => []),
          AdminUserService.getUserCouponRedemptions(userId).catch(() => [])
        ]);

        const fetchedOffers = Array.isArray(offersRes?.data) ? offersRes.data : (Array.isArray(offersRes) ? offersRes : []);
        const fetchedRedemptions = Array.isArray(redemptionsRes?.data) ? redemptionsRes.data : (Array.isArray(redemptionsRes) ? redemptionsRes : []);

        setOffers(fetchedOffers);
        // Sort redemptions by most recent
        setRedemptions(fetchedRedemptions.sort((a, b) => new Date(b.redeemed_at || 0) - new Date(a.redeemed_at || 0)));
      } catch (error) {
        console.error("Failed to load coupon data", error);
        toast.error("Could not load the user's coupons and history.");
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchCouponsData();
  }, [userId]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Skeleton className="h-[500px] w-full rounded-[2.5rem] bg-zinc-50" />
        <Skeleton className="h-[500px] w-full rounded-[2.5rem] bg-zinc-50" />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      
      {/* ========================================= */}
      {/* LEFT: PERSONALIZED OFFERS                 */}
      {/* ========================================= */}
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] overflow-hidden flex flex-col">
        <div className="p-8 border-b border-zinc-50 flex items-center gap-4 bg-zinc-50/30">
          <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center border border-zinc-100 text-zinc-900 shadow-sm">
            <Ticket size={20} />
          </div>
          <div>
            <h3 className="text-2xl font-serif font-bold text-zinc-900">Available Offers</h3>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-400 mt-1">Personalized For User</p>
          </div>
        </div>

        <div className="p-6 md:p-8 flex-1 bg-zinc-50/10">
          {offers.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-10">
              <Ticket size={32} className="text-zinc-300 mb-4" strokeWidth={1.5} />
              <p className="text-lg font-bold text-zinc-900 mb-1">No active offers</p>
              <p className="text-zinc-500 text-sm max-w-[250px]">This user currently has no personalized coupons available to claim.</p>
            </div>
          ) : (
            <div className="space-y-6">
              <AnimatePresence>
                {offers.map((offer, index) => {
                  const code = offer.code || "SPECIAL";
                  const discount = offer.discount_value || offer.discount_percentage || "10";
                  const isPercentage = offer.discount_type !== 'fixed';
                  const expiry = offer.expires_at ? new Date(offer.expires_at).toLocaleDateString() : 'No Expiry';

                  return (
                    <motion.div
                      key={offer.id || index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="group relative flex rounded-2xl border border-zinc-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                    >
                      {/* Ticket Left Side (Value) */}
                      <div className="bg-zinc-900 text-white p-6 flex flex-col items-center justify-center min-w-[120px] relative">
                        <Percent size={24} className="mb-2 text-zinc-400" />
                        <span className="text-3xl font-serif font-bold">{discount}{isPercentage ? '%' : '₹'}</span>
                        <span className="text-[10px] uppercase tracking-widest font-bold text-zinc-400 mt-1">OFF</span>
                        
                        {/* Decorative Ticket Cutouts */}
                        <div className="absolute -right-3 top-[-10px] w-6 h-6 bg-white rounded-full border border-zinc-200" />
                        <div className="absolute -right-3 bottom-[-10px] w-6 h-6 bg-white rounded-full border border-zinc-200" />
                      </div>
                      
                      {/* Ticket Right Side (Details) */}
                      <div className="p-6 flex-1 border-l border-dashed border-zinc-200 relative flex flex-col justify-center">
                        <div className="absolute -left-3 top-1/2 -translate-y-1/2 text-zinc-300">
                          <Scissors size={14} className="-rotate-90" />
                        </div>
                        
                        <Badge className="w-fit mb-3 bg-emerald-50 text-emerald-600 border-emerald-200 shadow-none text-[10px] font-bold uppercase tracking-widest px-2 py-1">
                          Active
                        </Badge>
                        <h4 className="text-lg font-bold text-zinc-900 mb-1 tracking-tight">{code}</h4>
                        <p className="text-xs font-medium text-zinc-500 flex items-center gap-1.5 mt-2">
                          <Calendar size={12} className="text-zinc-400" /> Valid until {expiry}
                        </p>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* ========================================= */}
      {/* RIGHT: REDEMPTION HISTORY                 */}
      {/* ========================================= */}
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] overflow-hidden flex flex-col">
        <div className="p-8 border-b border-zinc-50 flex items-center gap-4">
          <div className="w-12 h-12 bg-zinc-50 rounded-2xl flex items-center justify-center border border-zinc-100 text-zinc-400">
            <History size={20} />
          </div>
          <div>
            <h3 className="text-2xl font-serif font-bold text-zinc-900">Redemption History</h3>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-400 mt-1">Past Usage</p>
          </div>
        </div>

        <div className="p-6 md:p-8 flex-1">
          {redemptions.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-10">
              <AlertCircle size={32} className="text-zinc-300 mb-4" strokeWidth={1.5} />
              <p className="text-lg font-bold text-zinc-900 mb-1">No past redemptions</p>
              <p className="text-zinc-500 text-sm max-w-[250px]">This user hasn't used any discount codes or coupons yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {redemptions.map((redemption, index) => {
                  const code = redemption.coupon_code || redemption.code || "UNKNOWN";
                  const date = redemption.redeemed_at ? new Date(redemption.redeemed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Unknown Date';
                  const savings = redemption.discount_applied || redemption.savings || 0;
                  const orderId = redemption.order_id ? redemption.order_id.split('-')[0].toUpperCase() : 'N/A';

                  return (
                    <motion.div
                      key={redemption.id || index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-5 rounded-2xl border border-zinc-100 bg-zinc-50/50 hover:bg-white hover:shadow-md transition-all duration-300 flex items-center justify-between gap-4"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                          <CheckCircle2 size={18} />
                        </div>
                        <div>
                          <p className="font-bold text-zinc-900 text-sm tracking-tight">{code}</p>
                          <div className="flex items-center gap-3 mt-1 text-xs font-medium text-zinc-400">
                            <span className="flex items-center gap-1"><Calendar size={12} /> {date}</span>
                            <span className="w-1 h-1 rounded-full bg-zinc-300" />
                            <span className="flex items-center gap-1 font-mono"><ShoppingBag size={12} /> Ord: {orderId}</span>
                          </div>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1">Saved</p>
                        <p className="text-lg font-bold font-serif text-emerald-600 tracking-tight">₹{savings}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}