import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Award, Star, History, TrendingUp, 
  TrendingDown, Crown, Sparkles, Gift
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

// --- Helper to style tiers ---
const getTierStyling = (tier) => {
  const t = (tier || 'standard').toLowerCase();
  if (t.includes('gold') || t.includes('vip')) return { color: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20', icon: Crown };
  if (t.includes('platinum')) return { color: 'text-slate-200', bg: 'bg-slate-200/10', border: 'border-slate-200/20', icon: Sparkles };
  if (t.includes('silver')) return { color: 'text-zinc-300', bg: 'bg-zinc-300/10', border: 'border-zinc-300/20', icon: Star };
  return { color: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20', icon: Award };
};

export default function UserLoyalty({ userId }) {
  const [loyalty, setLoyalty] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLoyalty = async () => {
      try {
        setLoading(true);
        const res = await AdminUserService.getUserLoyalty(userId);
        const data = res?.data || res;
        
        // Handle if the API returns an array (ledger) or an object (summary)
        if (Array.isArray(data)) {
          // If it's an array, calculate total points and use it as history
          const totalPoints = data.reduce((sum, item) => sum + (item.points || 0), 0);
          setLoyalty({ points: totalPoints, tier: 'Standard Member' });
          setHistory(data.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)));
        } else if (data) {
          // If it's an object with summary + history
          setLoyalty({ points: data.points || 0, tier: data.tier || 'Standard Member' });
          setHistory(data.history || []);
        } else {
          setLoyalty({ points: 0, tier: 'Standard Member' });
          setHistory([]);
        }
      } catch (error) {
        console.error("Failed to load loyalty data", error);
        toast.error("Could not load the user's loyalty profile.");
        setLoyalty({ points: 0, tier: 'Standard Member' });
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchLoyalty();
  }, [userId]);

  if (loading) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-64 w-full rounded-[2.5rem] bg-zinc-50" />
        <Skeleton className="h-96 w-full rounded-[2.5rem] bg-zinc-50" />
      </div>
    );
  }

  const { icon: TierIcon, color: tierColor, bg: tierBg, border: tierBorder } = getTierStyling(loyalty?.tier);

  return (
    <div className="space-y-8">
      
      {/* --- LOYALTY SUMMARY CARD --- */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-zinc-900 text-white rounded-[2.5rem] p-8 md:p-12 shadow-2xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-8 border border-zinc-800"
      >
        {/* Luxury Background Glow */}
        <div className={`absolute top-0 right-0 w-96 h-96 ${tierBg} rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none`} />

        <div className="relative z-10 space-y-4 text-center md:text-left">
          <Badge className={`px-4 py-1.5 ${tierBg} ${tierColor} ${tierBorder} border font-black uppercase tracking-[0.2em] text-[10px] shadow-none flex items-center gap-2 mx-auto md:mx-0 w-fit`}>
            <TierIcon size={14} /> {loyalty.tier}
          </Badge>
          
          <div>
            <p className="text-zinc-400 text-[10px] font-bold uppercase tracking-[0.2em] mb-2">Total Points Balance</p>
            <h2 className="text-6xl md:text-8xl font-serif font-bold tracking-tighter text-white">
              {Number(loyalty.points).toLocaleString('en-US')}
            </h2>
          </div>
        </div>

        <div className="relative z-10 w-24 h-24 md:w-32 md:h-32 rounded-full bg-white/5 border border-white/10 flex items-center justify-center shadow-inner backdrop-blur-sm shrink-0">
          <Gift size={48} className={tierColor} strokeWidth={1.5} />
        </div>
      </motion.div>

      {/* --- RECENT ACTIVITY --- */}
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] overflow-hidden">
        <div className="p-8 border-b border-zinc-50 flex items-center gap-4">
          <div className="w-12 h-12 bg-zinc-50 rounded-2xl flex items-center justify-center border border-zinc-100 text-zinc-400">
            <History size={20} />
          </div>
          <div>
            <h3 className="text-2xl font-serif font-bold text-zinc-900">Point Activity</h3>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-400 mt-1">Recent Transactions</p>
          </div>
        </div>

        <div className="p-4 md:p-8">
          {history.length === 0 ? (
            <div className="py-12 flex flex-col items-center justify-center text-center">
              <Award size={32} className="text-zinc-300 mb-4" strokeWidth={1.5} />
              <p className="text-lg font-bold text-zinc-900 mb-1">No point activity yet</p>
              <p className="text-zinc-500 text-sm">Points earned from purchases or reviews will appear here.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {history.map((item, index) => {
                  const points = item.points || 0;
                  const isPositive = points > 0;
                  const date = item.created_at ? new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recent';
                  
                  return (
                    <motion.div
                      key={item.id || index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center justify-between p-5 rounded-2xl border border-zinc-100 bg-zinc-50/50 hover:bg-white hover:shadow-md transition-all duration-300"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isPositive ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>
                          {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                        </div>
                        <div>
                          <p className="font-bold text-zinc-900 text-sm">{item.reason || item.description || (isPositive ? 'Points Earned' : 'Points Redeemed')}</p>
                          <p className="text-xs font-medium text-zinc-400 mt-0.5">{date}</p>
                        </div>
                      </div>
                      <div className={`text-lg font-bold font-serif tracking-tight ${isPositive ? 'text-emerald-600' : 'text-zinc-900'}`}>
                        {isPositive ? '+' : ''}{points}
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