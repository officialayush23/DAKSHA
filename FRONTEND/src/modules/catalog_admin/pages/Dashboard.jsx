// src/modules/catalog_admin/pages/Dashboard.jsx

import React, { useEffect, useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { motion } from "framer-motion"; 
import { 
  Package, Layers, AlertTriangle, TrendingUp, Plus, Search, ArrowRight, Loader2, ShieldCheck
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/apiClient"; 

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

const containerVar = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
const itemVar = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

export default function Dashboard() {
  const navigate = useNavigate();
  const { admin } = useOutletContext(); 

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    stats: { total_products: 0, total_variants: 0, total_categories: 0, missing_images: 0 },
    recent_products: [],
    categories: []
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!admin) return;

      try {
        setLoading(true);
        const res = await api.get("/admin/catalog/dashboard");
        
        console.log("📊 Dashboard Response:", res.data); // DEBUG LOG

        if (res.data) {
            setData(res.data);
        }
      } catch (error) {
        console.error("Dashboard fetch error:", error);
        if (error.code !== "ERR_NETWORK") {
             toast.error("Failed to load dashboard data.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [admin]);

  // ... (Rest of JSX is identical to your provided code) ...
  return (
    <div className="w-full bg-black text-white font-sans selection:bg-zinc-800 animate-in fade-in">
      <div className="fixed top-0 left-0 w-full h-[500px] bg-gradient-to-b from-zinc-900/20 to-transparent pointer-events-none -z-10" />

      <motion.div variants={containerVar} initial="hidden" animate="show" className="max-w-[1600px] mx-auto space-y-8">
        
        {/* HEADER */}
        <motion.div variants={itemVar} className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h2 className="text-4xl font-bold tracking-tight text-white mb-2">Command Center</h2>
            <div className="flex items-center gap-2 text-zinc-400 font-medium">
               <ShieldCheck className="h-4 w-4 text-emerald-500"/>
               <span>Welcome back, {admin?.full_name || "Admin"}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="h-10 border-zinc-800 bg-black/50 text-zinc-300 hover:bg-zinc-900" onClick={() => navigate("/catalog/search")}>
              <Search className="mr-2 h-4 w-4" /> Search 
            </Button>
            <Button className="h-10 bg-white text-black hover:bg-zinc-200" onClick={() => navigate("/catalog/create-product")}>
              <Plus className="mr-2 h-4 w-4" /> Create Product
            </Button>
          </div>
        </motion.div>

        {/* STATS GRID */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatsCard title="Total Products" value={data.stats.total_products} icon={Package} desc="Parent definitions" loading={loading} />
          <StatsCard title="Total Variants" value={data.stats.total_variants} icon={Layers} desc="Physical SKUs" loading={loading} />
          <StatsCard title="Missing Images" value={data.stats.missing_images} icon={AlertTriangle} desc="Requires attention" loading={loading} isAlert={data.stats.missing_images > 0} />
          <StatsCard title="Categories" value={data.stats.total_categories} icon={TrendingUp} desc="Active classifications" loading={loading} />
        </div>

        {/* SPLIT VIEW */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
          
          {/* RECENT PRODUCTS */}
          <motion.div variants={itemVar} className="col-span-4 rounded-xl border border-zinc-800 bg-zinc-950/50 backdrop-blur-sm overflow-hidden">
            <div className="p-6 border-b border-zinc-800/50 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
              <Button variant="ghost" size="sm" onClick={() => navigate('/catalog/list')} className="text-zinc-400 hover:text-white">View All <ArrowRight className="ml-2 h-4 w-4" /></Button>
            </div>
            
            <div className="relative">
              {loading ? (
                 <div className="p-6 space-y-4">
                   {[1,2,3].map(i => <Skeleton key={i} className="h-12 w-full bg-zinc-900 rounded-lg" />)}
                 </div>
              ) : data.recent_products.length === 0 ? (
                 <div className="p-12 text-center text-zinc-500">No recent activity.</div>
              ) : (
                <div className="divide-y divide-zinc-800/50">
                  {data.recent_products.map((product) => (
                    <div key={product.id} className="group flex items-center justify-between p-4 hover:bg-zinc-900/80 transition-colors cursor-pointer" onClick={() => navigate(`/catalog/create-variant?product_id=${product.id}`)}>
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 font-mono text-xs group-hover:border-zinc-600 transition-colors">{product.name.charAt(0)}</div>
                        <div>
                          <p className="text-sm font-medium text-white group-hover:text-emerald-400 transition-colors">{product.name}</p>
                          <p className="text-xs text-zinc-500 font-mono">ID: {product.id.slice(0, 8)}...</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge variant="secondary" className="bg-zinc-900 text-zinc-400 border-zinc-800">{product.categories?.name || "N/A"}</Badge>
                        <span className="text-sm font-medium text-zinc-300 w-20 text-right">₹{product.base_price}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>

          {/* QUICK CATEGORIES */}
          <motion.div variants={itemVar} className="col-span-3 rounded-xl border border-zinc-800 bg-zinc-950/50 backdrop-blur-sm p-6 flex flex-col">
            <h3 className="text-lg font-semibold text-white mb-6">Categories</h3>
            <div className="space-y-3 flex-1">
              {loading ? <Skeleton className="h-40 w-full bg-zinc-900" /> : (
                data.categories.length > 0 ? (
                  data.categories.map((cat, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-zinc-900/30 border border-transparent hover:border-zinc-700 hover:bg-zinc-900 transition-all cursor-pointer">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-2 rounded-full bg-emerald-500" />
                        <span className="text-sm font-medium text-zinc-300">{cat.name}</span>
                      </div>
                      <span className="text-xs text-zinc-600 font-mono uppercase tracking-wider">{cat.slug}</span>
                    </div>
                  ))
                ) : <div className="text-sm text-zinc-500 text-center py-4">No categories found.</div>
              )}
            </div>
            <Button variant="outline" className="w-full mt-6 border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-900" onClick={() => navigate("/catalog/categories")}>Manage Structure</Button>
          </motion.div>

        </div>
      </motion.div>
    </div>
  );
}

function StatsCard({ title, value, icon: Icon, desc, loading, isAlert }) {
  return (
    <motion.div variants={itemVar} className={`relative overflow-hidden rounded-xl border bg-zinc-950/50 p-6 transition-all hover:bg-zinc-900/80 ${isAlert ? 'border-red-900/30' : 'border-zinc-800'}`}>
      <div className="flex items-center justify-between space-y-0 pb-2">
        <p className="text-sm font-medium text-zinc-400">{title}</p>
        <div className={`p-2 rounded-lg ${isAlert ? 'bg-red-950/50 text-red-500' : 'bg-zinc-900 text-zinc-500'}`}><Icon className="h-4 w-4" /></div>
      </div>
      <div className="mt-2">
        {loading ? <Skeleton className="h-8 w-16 bg-zinc-800" /> : <div className="flex items-baseline gap-2"><span className={`text-3xl font-bold ${isAlert ? 'text-red-500 drop-shadow-[0_0_10px_rgba(239,68,68,0.3)]' : 'text-white'}`}>{value}</span></div>}
        <p className="text-xs text-zinc-500 mt-1">{desc}</p>
      </div>
      <div className={`absolute -right-6 -bottom-6 h-24 w-24 rounded-full blur-3xl opacity-10 pointer-events-none ${isAlert ? 'bg-red-500' : 'bg-white'}`} />
    </motion.div>
  );
}