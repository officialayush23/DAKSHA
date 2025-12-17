import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/apiClient"; 
import { motion } from "framer-motion";
import { 
  LifeBuoy, CheckCircle, Clock, ArrowRight, Activity 
} from "lucide-react";
import { toast } from "sonner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

// Animations
const containerVar = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
const itemVar = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

export default function SupportDashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    open_count: 0,
    resolved_count: 0
  });

  // Fetch Stats from Backend
  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      try {
        const res = await api.get("/admin/support/stats");
        setStats(res.data);
      } catch (error) {
        console.error("Stats Error:", error);
        toast.error("Failed to load support stats.");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="w-full space-y-8 animate-in fade-in">
      
      {/* HEADER */}
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-bold tracking-tight text-white">Support Center</h2>
        <p className="text-zinc-400">
          Overview of current ticket volume and resolution metrics.
        </p>
      </div>

      {/* STATS GRID */}
      <motion.div 
        variants={containerVar}
        initial="hidden"
        animate="show"
        className="grid gap-4 md:grid-cols-3"
      >
        <StatsCard 
          title="Open Tickets" 
          value={stats.open_count} 
          icon={LifeBuoy} 
          desc="Requiring attention" 
          loading={loading}
          alert={stats.open_count > 5} // Highlight if backlog is high
          color="text-indigo-500" 
        />
        
        <StatsCard 
          title="Resolved (Human)" 
          value={stats.resolved_count} 
          icon={CheckCircle} 
          desc="Closed by agents" 
          loading={loading}
          color="text-emerald-500"
        />
        
        <StatsCard 
          title="Dynamic Support" 
          value="98%" 
          icon={Activity} 
          desc="Based on SLA adherence" 
          loading={loading}
          color="text-blue-500"
        />
      </motion.div>

      {/* ACTION AREA */}
      <div className="grid gap-6 md:grid-cols-2">
        
        {/* Quick Actions */}
        <Card className="bg-zinc-950 border-zinc-800 text-white">
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Link to="/support-agent/tickets">
              <Button className="w-full bg-indigo-600 hover:bg-indigo-700 text-white h-12 text-base justify-between group">
                <span className="flex items-center gap-2"><LifeBuoy className="h-5 w-5"/> Go to Inbox</span>
                <ArrowRight className="h-5 w-5 opacity-70 group-hover:translate-x-1 transition-transform"/>
              </Button>
            </Link>
            
            <div className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-900 flex gap-3 items-start">
              <Clock className="h-5 w-5 text-zinc-500 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium text-zinc-300">SLA Warning</p>
                <p className="text-xs text-zinc-500">
                  Tickets open for longer than 24 hours will be flagged automatically. 
                  Currently 0 tickets at risk.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="bg-zinc-950 border-zinc-800 text-white flex flex-col justify-center items-center text-center p-6">
           <div className="bg-zinc-900 p-4 rounded-full mb-4">
             <CheckCircle className="h-8 w-8 text-emerald-500" />
           </div>
           <h3 className="text-lg font-semibold text-white">System Healthy</h3>
           <p className="text-zinc-500 text-sm mt-2 max-w-xs">
             
           </p>
        </Card>

      </div>
    </div>
  );
}

function StatsCard({ title, value, icon: Icon, desc, loading, alert, color }) {
  return (
    <motion.div variants={itemVar}>
      <Card className={`bg-zinc-950 border-zinc-800 text-white overflow-hidden relative transition-all hover:border-zinc-700 ${alert ? 'border-indigo-500/50' : ''}`}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between pb-2">
            <p className="text-sm font-medium text-zinc-400">{title}</p>
            <div className={`p-2 rounded-lg bg-zinc-900 ${color}`}><Icon className="h-4 w-4" /></div>
          </div>
          <div className="mt-2">
            {loading ? <Skeleton className="h-8 w-16 bg-zinc-800" /> : <div className={`text-3xl font-bold ${alert ? 'text-indigo-400' : 'text-white'}`}>{value}</div>}
            <p className="text-xs text-zinc-500 mt-1">{desc}</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}