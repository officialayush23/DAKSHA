import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, ArrowLeft, ShieldCheck } from 'lucide-react';

export default function AdminUserLayout() {
  const location = useLocation();
  
  // Check if we are on a specific user's detail page or the main list
  const isDetailPage = location.pathname.split('/').length > 3;

  return (
    <div className="flex-1 flex flex-col w-full bg-[#FCFCFC] min-h-full font-sans text-zinc-900 selection:bg-black selection:text-white">
      
      {/* --- CRM Sub-Header --- */}
      <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-zinc-100 px-6 py-4 flex items-center justify-between shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-4">
          <AnimatePresence mode="popLayout">
            {isDetailPage && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, x: -10 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.8, x: -10 }}
              >
                <Link 
                  to="/admin/users" 
                  className="w-10 h-10 flex items-center justify-center rounded-full bg-zinc-50 border border-zinc-200 text-zinc-500 hover:text-black hover:bg-white hover:shadow-md transition-all duration-300"
                >
                  <ArrowLeft size={18} />
                </Link>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-zinc-900 text-white flex items-center justify-center shadow-lg">
              <Users size={20} />
            </div>
            <div>
              <h1 className="text-xl font-serif font-bold tracking-tight text-zinc-900 leading-none">
                Customer Directory
              </h1>
              <p className="text-[10px] uppercase tracking-widest text-zinc-400 font-bold mt-1 flex items-center gap-1">
                <ShieldCheck size={12} className="text-emerald-500" /> Admin Module
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* --- Page Content (Outlet for List & Detail Pages) --- */}
      <main className="flex-1 w-full max-w-[1600px] mx-auto p-4 md:p-8 xl:p-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="h-full"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

    </div>
  );
}