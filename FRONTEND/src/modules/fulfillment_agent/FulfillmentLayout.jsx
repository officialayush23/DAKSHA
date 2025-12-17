// src/modules/fulfillment_agent/FulfillmentLayout.jsx

import React, { useEffect, useState } from "react";
import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { 
  Package, ClipboardList, Archive, LogOut, MapPin, Loader2, Check, ChevronsUpDown, AlertTriangle 
} from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarHeader, SidebarFooter, SidebarProvider, SidebarTrigger
} from "@/components/ui/sidebar";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { supabase } from "@/lib/supabaseClient";
import { toast } from "sonner";

export default function FulfillmentLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [locations, setLocations] = useState([]);
  const [activeLocation, setActiveLocation] = useState(null);

  useEffect(() => {
    const initSession = async () => {
      try {
        // 1. Check Login
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) { navigate("/login"); return; }

        // 2. Fetch User Roles & Assignments
        // We fetch stores(name) to display the friendly name in the dropdown
        const { data: roles, error } = await supabase
          .from('user_roles')
          .select(`
            role, 
            store_id, 
            warehouse_id, 
            stores ( name )
          `) 
          .eq('user_id', user.id);

        if (error) throw error;

        // 3. Security Check
        const isAuthorized = roles?.some(r => r.role === 'fulfillment_agent' || r.role === 'super_admin');
        if (!isAuthorized) {
          navigate("/unauthorized");
          return;
        }

        // 4. Extract Valid Locations
        const availableLocations = roles
          .filter(r => r.store_id || r.warehouse_id)
          .map(r => ({
            id: r.store_id || r.warehouse_id,
            name: r.stores?.name || (r.store_id ? "Unknown Store" : "Warehouse"), // Fallback name
            type: r.store_id ? "store" : "warehouse"
          }));

        // Remove duplicates (in case user has multiple roles for same location)
        const uniqueLocations = Array.from(new Map(availableLocations.map(item => [item.id, item])).values());

        setLocations(uniqueLocations);

        // 5. Set Active Location (Restore from Storage or Default to First)
        if (uniqueLocations.length > 0) {
          const savedId = localStorage.getItem("active_fulfillment_id");
          const found = uniqueLocations.find(l => l.id === savedId);
          const initial = found || uniqueLocations[0];
          
          setActiveLocation(initial);
          // Ensure storage is synced if we fell back to default
          if (!found) localStorage.setItem("active_fulfillment_id", initial.id);
        }

      } catch (err) {
        console.error("Session Init Error:", err);
        toast.error("Failed to load user profile.");
      } finally {
        setLoading(false);
      }
    };

    initSession();
  }, [navigate]);

  const handleLocationChange = (loc) => {
    setActiveLocation(loc);
    localStorage.setItem("active_fulfillment_id", loc.id);
    toast.success(`Switched to ${loc.name}`);
    // Optional: Refresh page to force all children to reload with new context
    // window.location.reload(); 
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate("/login");
  };

  if (loading) {
    return (
      <div className="h-screen w-full bg-black flex items-center justify-center text-zinc-500">
        <Loader2 className="animate-spin mr-2 h-6 w-6 text-amber-500" /> Verifying Access...
      </div>
    );
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-black text-white font-sans selection:bg-amber-500/30">
        
        {/* SIDEBAR */}
        <Sidebar collapsible="icon" className="border-r border-zinc-800 bg-black">
          <SidebarHeader className="border-b border-zinc-900 bg-black p-4">
            <div className="flex items-center gap-2 font-bold text-white">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-600 text-white">
                <Package className="h-5 w-5" />
              </div>
              <span className="truncate">Logistics Hub</span>
            </div>
          </SidebarHeader>

          <SidebarContent className="bg-black p-2">
            
            {/* LOCATION SELECTOR */}
            <div className="mb-6 px-2">
              <label className="text-[10px] uppercase text-zinc-500 font-bold mb-1.5 block px-1">
                Current Location
              </label>
              {locations.length > 0 ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="w-full justify-between bg-zinc-900 border-zinc-800 text-zinc-300 hover:text-white hover:bg-zinc-800 h-9 px-3 text-xs">
                      <div className="flex items-center gap-2 truncate">
                        <MapPin className="h-3.5 w-3.5 text-amber-500" />
                        <span className="truncate max-w-[120px]">{activeLocation?.name}</span>
                      </div>
                      <ChevronsUpDown className="h-3 w-3 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56 bg-zinc-950 border-zinc-800 text-white">
                    {locations.map((loc) => (
                      <DropdownMenuItem 
                        key={loc.id} 
                        onClick={() => handleLocationChange(loc)}
                        className="flex items-center justify-between cursor-pointer focus:bg-zinc-900 focus:text-white"
                      >
                        <span className="text-xs">{loc.name}</span>
                        {activeLocation?.id === loc.id && <Check className="h-3 w-3 text-amber-500" />}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <div className="flex items-center gap-2 text-red-400 text-xs px-2 py-2 border border-red-900/30 bg-red-950/10 rounded">
                  <AlertTriangle className="h-3 w-3" />
                  <span>No assigned location</span>
                </div>
              )}
            </div>

            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton 
                      asChild 
                      isActive={location.pathname === "/fulfillment-agent"}
                      className="text-zinc-400 hover:text-white hover:bg-zinc-900 data-[active=true]:bg-zinc-800 data-[active=true]:text-white h-10 transition-colors"
                    >
                      <Link to="/fulfillment-agent">
                        <ClipboardList className="h-4 w-4" />
                        <span>Active Queue</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton 
                      asChild 
                      isActive={location.pathname === "/fulfillment-agent/history"}
                      className="text-zinc-400 hover:text-white hover:bg-zinc-900 data-[active=true]:bg-zinc-800 data-[active=true]:text-white h-10 transition-colors"
                    >
                      <Link to="/fulfillment-agent/history">
                        <Archive className="h-4 w-4" />
                        <span>Shipped History</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="bg-black border-t border-zinc-900 p-2">
            <SidebarMenuButton onClick={handleLogout} className="text-red-400 hover:text-red-300 hover:bg-red-950/20 group">
              <LogOut className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              <span>End Shift</span>
            </SidebarMenuButton>
          </SidebarFooter>
        </Sidebar>

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 flex flex-col min-w-0">
          <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b border-zinc-900 bg-black/80 px-4 backdrop-blur-md">
            <SidebarTrigger className="-ml-1 text-zinc-400 hover:text-white" />
            <Separator orientation="vertical" className="mr-2 h-4 bg-zinc-800" />
            <span className="text-sm font-medium text-zinc-300">Order Fulfillment Console</span>
          </header>

          <div className="flex-1 w-full bg-black p-6 overflow-auto">
            {/* PASS THE ACTIVE LOCATION ID TO CHILDREN */}
            {activeLocation ? (
              <Outlet context={{ locationId: activeLocation.id }} />
            ) : (
               <div className="h-full flex flex-col items-center justify-center text-zinc-500">
                  <AlertTriangle className="h-10 w-10 mb-4 opacity-20" />
                  <p>Please contact your manager to assign a Warehouse or Store to your account.</p>
               </div>
            )}
          </div>
        </main>

      </div>
    </SidebarProvider>
  );
}