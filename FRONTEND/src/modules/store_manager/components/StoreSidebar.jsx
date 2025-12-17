
// src/modules/store_manager/components/StoreSidebar.jsx

import React from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  LayoutDashboard, 
  ArrowDownToLine, 
  PackageCheck, 
  Store,
  ChevronRight,
  Settings,
  History,
  List // <--- Imported new icon
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarRail,
  useSidebar
} from "@/components/ui/sidebar";

const items = [
  { 
    title: "Overview", 
    url: "/store-manager", 
    icon: LayoutDashboard 
  },
  { 
    title: "Inward Stock", 
    url: "/store-manager/inward", 
    icon: ArrowDownToLine 
  },
  { 
    title: "Inventory List", // <--- New Page Link
    url: "/store-manager/list", 
    icon: List 
  },
  { 
    title: "Order Queue", 
    url: "/store-manager/orders", 
    icon: PackageCheck 
  },
  { 
    title: "History Logs", 
    url: "/store-manager/history", 
    icon: History 
  },
];

export default function StoreSidebar() {
  const location = useLocation();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  return (
    <Sidebar collapsible="icon" className="border-r border-zinc-800 bg-black text-white">
      
      {/* --- BRAND HEADER --- */}
      <SidebarHeader className="h-16 flex items-center justify-center border-b border-zinc-900/50">
        <div className="flex items-center gap-3 w-full px-2 transition-all duration-500">
          <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <Store className="h-5 w-5 text-black" />
          </div>
          
          {!isCollapsed && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex flex-col"
            >
              <span className="text-sm font-bold tracking-wide text-white">Store Ops</span>
              <span className="text-[10px] font-medium tracking-widest text-zinc-500 uppercase">Pune Branch</span>
            </motion.div>
          )}
        </div>
      </SidebarHeader>
      
      {/* --- NAVIGATION CONTENT --- */}
      <SidebarContent className="px-3 py-6">
        <div className="flex flex-col gap-1">
          {/* Label */}
          {!isCollapsed && (
            <motion.span 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              className="px-3 text-[11px] font-semibold uppercase tracking-widest text-zinc-600 mb-2 pl-4"
            >
              Daily Operations
            </motion.span>
          )}

          <AnimatePresence>
            {items.map((item, idx) => {
              const isActive = location.pathname === item.url;
              
              return (
                <Link 
                  key={item.url} 
                  to={item.url}
                  className="relative group flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-300 ease-out outline-none"
                >
                  {/* Active Indicator (Glow Line) */}
                  {isActive && (
                    <motion.div
                      layoutId="active-glow-store"
                      className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-0.5 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]"
                    />
                  )}

                  {/* Active Background */}
                  {isActive && (
                    <div className="absolute inset-0 rounded-lg bg-zinc-900 border border-zinc-800/50" />
                  )}

                  {/* Icon */}
                  <item.icon 
                    className={`relative z-10 h-5 w-5 transition-colors duration-300 ${
                      isActive ? "text-emerald-400 drop-shadow-md" : "text-zinc-500 group-hover:text-zinc-300"
                    }`} 
                  />

                  {/* Text Label */}
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.05 * idx }}
                      className={`relative z-10 text-sm font-medium transition-colors duration-300 ${
                        isActive ? "text-white" : "text-zinc-400 group-hover:text-zinc-200"
                      }`}
                    >
                      {item.title}
                    </motion.span>
                  )}

                  {/* Chevron */}
                  {isActive && !isCollapsed && (
                    <motion.div 
                      initial={{ opacity: 0, x: -5 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="ml-auto"
                    >
                      <ChevronRight className="h-3 w-3 text-emerald-500" />
                    </motion.div>
                  )}
                </Link>
              );
            })}
          </AnimatePresence>
        </div>
      </SidebarContent>

      {/* --- FOOTER --- */}
      <SidebarFooter className="p-4 border-t border-zinc-900/50">
        <button className="group flex items-center gap-3 w-full rounded-lg p-2 hover:bg-zinc-900 transition-colors">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-zinc-400 group-hover:text-white group-hover:bg-zinc-700 transition-colors">
            <Settings className="h-4 w-4" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col items-start overflow-hidden">
              <span className="text-sm font-medium text-zinc-300 group-hover:text-white truncate">Settings</span>
              <span className="text-[10px] text-zinc-500 truncate">Printer & Scanner</span>
            </div>
          )}
        </button>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}