//  src/modules/super_admin/SuperAdminLayout.jsx

import React from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import { ShieldCheck, MapPin, Users, Package, LogOut } from "lucide-react";
import { supabase } from '@/lib/supabaseClient';

export default function SuperAdminLayout() {
  const location = useLocation();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    window.location.href = "/login";
  };

  const navItems = [
    { name: "Create Locations", path: "/super-admin", icon: MapPin },
    { name: "Access Control (RBAC)", path: "/super-admin/rbac", icon: Users },
  ];

  return (
    <div className="min-h-screen bg-black text-white flex font-sans selection:bg-indigo-500/30">
      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col">
        <div className="h-16 flex items-center gap-2 px-6 border-b border-zinc-900">
          <ShieldCheck className="h-6 w-6 text-indigo-500" />
          <span className="font-bold tracking-tight text-lg">Super Admin</span>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive 
                    ? " text-white" 
                    : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
                }`}
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-zinc-900">
          <button 
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-red-400 hover:text-red-300 w-full hover:bg-red-950/20 rounded-lg transition-colors"
          >
            <LogOut className="h-4 w-4" /> Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-black">
        <div className="p-8 max-w-5xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}