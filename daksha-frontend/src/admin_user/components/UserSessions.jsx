import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, Monitor, Smartphone, 
  Store, Clock, Power, History 
} from 'lucide-react';
import { AdminUserService } from '@/lib/adminUserService';
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { toast } from 'sonner';

// --- Helper: Channel Icon & Styling ---
const getChannelConfig = (channel) => {
  const c = (channel || "web").toLowerCase();
  if (c.includes('app') || c.includes('mobile')) {
    return { icon: Smartphone, color: 'text-blue-500 bg-blue-50 border-blue-100', label: 'Mobile App' };
  }
  if (c.includes('kiosk') || c.includes('pos')) {
    return { icon: Store, color: 'text-purple-500 bg-purple-50 border-purple-100', label: 'In-Store Kiosk' };
  }
  return { icon: Monitor, color: 'text-zinc-600 bg-zinc-100 border-zinc-200', label: 'Web Browser' };
};

export default function UserSessions({ userId }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        setLoading(true);
        const res = await AdminUserService.getUserSessions(userId);
        const fetchedSessions = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
        
        // Sort by newest session first
        const sorted = fetchedSessions.sort((a, b) => new Date(b.started_at || 0) - new Date(a.started_at || 0));
        setSessions(sorted);
      } catch (error) {
        console.error("Failed to load user sessions", error);
        toast.error("Could not load session history.");
      } finally {
        setLoading(false);
      }
    };

    if (userId) fetchSessions();
  }, [userId]);

  // --- RENDER HELPERS ---
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4].map(i => (
          <Skeleton key={i} className="h-48 w-full rounded-[2rem] bg-zinc-50" />
        ))}
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] min-h-[400px] flex flex-col items-center justify-center text-center p-10">
        <div className="w-20 h-20 bg-zinc-50 rounded-full flex items-center justify-center mb-6 border border-zinc-100">
          <History size={32} className="text-zinc-300" strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-serif font-bold text-zinc-900 mb-2">No Session History</h3>
        <p className="text-zinc-500 max-w-sm">There are no recorded sessions for this user yet.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <AnimatePresence>
        {sessions.map((session, index) => {
          const sessionId = session.id;
          const displayId = sessionId ? sessionId.split('-')[0].toUpperCase() : "UNKNOWN";
          
          const startDate = new Date(session.started_at);
          const formattedDate = startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
          const formattedTime = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
          
          const isActive = !session.ended_at;
          const { icon: ChannelIcon, color: channelColor, label: channelLabel } = getChannelConfig(session.primary_channel || session.active_channel);

          return (
            <motion.div
              key={sessionId || index}
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.4 }}
              className="group relative bg-white rounded-[2rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] p-6 md:p-8 hover:shadow-xl hover:border-zinc-200 transition-all duration-300 flex flex-col"
            >
              
              {/* Header: Status & Channel */}
              <div className="flex justify-between items-start mb-6">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${channelColor}`}>
                  <ChannelIcon size={20} />
                </div>
                
                {isActive ? (
                  <Badge className="px-3 py-1 bg-emerald-50 text-emerald-600 border-emerald-200 shadow-none font-bold uppercase tracking-widest text-[10px] flex items-center gap-1.5 animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Active Now
                  </Badge>
                ) : (
                  <Badge className="px-3 py-1 bg-zinc-50 text-zinc-400 border-zinc-200 shadow-none font-bold uppercase tracking-widest text-[10px] flex items-center gap-1.5">
                    <Power size={10} /> Ended
                  </Badge>
                )}
              </div>

              {/* Body: Session Details */}
              <div className="flex-1 space-y-4">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1">Platform</p>
                  <h3 className="text-xl font-bold text-zinc-900">{channelLabel}</h3>
                  <p className="text-xs font-mono text-zinc-400 mt-1">ID: {displayId}</p>
                </div>

                <div className="pt-4 border-t border-zinc-50 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5 flex items-center gap-1.5">
                      <Clock size={12} /> Started
                    </p>
                    <p className="text-sm font-bold text-zinc-700">{formattedTime}</p>
                    <p className="text-xs font-medium text-zinc-400">{formattedDate}</p>
                  </div>
                  
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400 mb-1.5 flex items-center gap-1.5">
                      <Activity size={12} /> Status
                    </p>
                    <p className={`text-sm font-bold ${isActive ? 'text-emerald-600' : 'text-zinc-500'}`}>
                      {isActive ? 'In Progress' : 'Completed'}
                    </p>
                    {session.ended_at && (
                      <p className="text-xs font-medium text-zinc-400">
                        {new Date(session.ended_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    )}
                  </div>
                </div>
              </div>

            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}