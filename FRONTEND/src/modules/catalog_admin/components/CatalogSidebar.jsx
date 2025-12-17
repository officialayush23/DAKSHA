import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Library, 
  PlusCircle, 
  Layers, 
  Tag, 
  LayoutDashboard,
  Box,
  ChevronRight,
  Settings
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
  { title: "Dashboard", url: "/catalog", icon: LayoutDashboard },
  { title: "All Products", url: "/catalog/list", icon: Library },
  { title: "New Product", url: "/catalog/create-product", icon: PlusCircle },
  { title: "Variants", url: "/catalog/create-variant", icon: Layers },
  { title: "Categories", url: "/catalog/categories", icon: Tag },
];

export default function CatalogSidebar() {
  const location = useLocation();
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";
  const [hoveredIndex, setHoveredIndex] = useState(null);

  return (
    <Sidebar collapsible="icon" className="border-r border-zinc-800 bg-black text-white">
      
      {/* --- BRAND HEADER --- */}
      <SidebarHeader className="h-16 flex items-center justify-center border-b border-zinc-900/50">
        <div className="flex items-center gap-3 w-full px-2 transition-all duration-500">
          <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-white to-zinc-400 shadow-[0_0_15px_rgba(255,255,255,0.15)]">
            <Box className="h-5 w-5 text-black" />
          </div>
          
          {!isCollapsed && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex flex-col"
            >
              <span className="text-sm font-bold tracking-wide text-white">Catalog</span>
              <span className="text-[10px] font-medium tracking-widest text-zinc-500 uppercase">Admin v2.0</span>
            </motion.div>
          )}
        </div>
      </SidebarHeader>
      
      {/* --- NAVIGATION CONTENT --- */}
      <SidebarContent className="px-3 py-6">
        <div className="flex flex-col gap-1">
          {/* Label only visible when expanded */}
          {!isCollapsed && (
            <motion.span 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              className="px-3 text-[11px] font-semibold uppercase tracking-widest text-zinc-600 mb-2 pl-4"
            >
              Management
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
                  onMouseEnter={() => setHoveredIndex(idx)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  {/* Active Indicator (Glow Line) */}
                  {isActive && (
                    <motion.div
                      layoutId="active-glow"
                      className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-0.5 rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)]"
                      initial={{ height: 0 }}
                      animate={{ height: 20 }}
                    />
                  )}

                  {/* Hover Background Pill (Smooth slide) */}
                  {hoveredIndex === idx && !isActive && (
                    <motion.div
                      layoutId="hover-pill"
                      className="absolute inset-0 rounded-lg bg-zinc-900/60"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}

                  {/* Active Background (Static) */}
                  {isActive && (
                    <div className="absolute inset-0 rounded-lg bg-zinc-900 border border-zinc-800/50" />
                  )}

                  {/* Icon */}
                  <item.icon 
                    className={`relative z-10 h-5 w-5 transition-colors duration-300 ${
                      isActive ? "text-white drop-shadow-md" : "text-zinc-500 group-hover:text-zinc-300"
                    }`} 
                  />

                  {/* Text Label */}
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * idx }} // Stagger effect
                      className={`relative z-10 text-sm font-medium transition-colors duration-300 ${
                        isActive ? "text-white" : "text-zinc-400 group-hover:text-zinc-200"
                      }`}
                    >
                      {item.title}
                    </motion.span>
                  )}

                  {/* Chevron for Active */}
                  {isActive && !isCollapsed && (
                    <motion.div 
                      initial={{ opacity: 0, x: -5 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="ml-auto"
                    >
                      <ChevronRight className="h-3 w-3 text-zinc-500" />
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
              <span className="text-[10px] text-zinc-500 truncate">Preferences</span>
            </div>
          )}
        </button>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}