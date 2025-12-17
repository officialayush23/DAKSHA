import React, { useEffect, useState } from "react";
import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { 
  Factory, LayoutDashboard, PackageSearch, Truck, LogOut, Check, ChevronsUpDown, AlertTriangle, Loader2 
} from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarHeader, SidebarFooter, SidebarProvider, SidebarTrigger
} from "@/components/ui/sidebar";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { supabase } from "@/lib/supabaseClient";
import { toast } from "sonner";

export default function WarehouseLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [warehouses, setWarehouses] = useState([]);
  const [activeWarehouse, setActiveWarehouse] = useState(null);

  useEffect(() => {
    const init = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) { navigate("/login"); return; }

        // Fetch Warehouse Roles
        const { data: roles } = await supabase
          .from('user_roles')
          .select('warehouse_id, role, warehouses(name)') 
          .eq('user_id', user.id);

        const isManager = roles?.some(r => r.role === 'warehouse_manager');
        const userCheck = await supabase.from('users').select('role').eq('id', user.id).single();
        const isSuper = userCheck.data?.role === 'super_admin';

        if (!isManager && !isSuper) {
           navigate("/unauthorized");
           return;
        }

        // Format List
        let available = roles
            ?.filter(r => r.warehouse_id)
            .map(r => ({
                id: r.warehouse_id,
                name: r.warehouses?.name || "Warehouse " + r.warehouse_id.slice(0,4)
            })) || [];
        
        // Remove duplicates
        available = Array.from(new Map(available.map(item => [item.id, item])).values());

        setWarehouses(available);

        // Restore Selection
        if (available.length > 0) {
          const saved = localStorage.getItem("active_warehouse_id");
          const found = available.find(w => w.id === saved);
          setActiveWarehouse(found || available[0]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [navigate]);

  const handleSwitch = (wh) => {
    setActiveWarehouse(wh);
    localStorage.setItem("active_warehouse_id", wh.id);
    toast.success(`Switched to ${wh.name}`);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate("/login");
  };

  if (loading) return <div className="h-screen bg-zinc-950 flex items-center justify-center text-zinc-500"><Loader2 className="animate-spin mr-2"/> Accessing Facility...</div>;

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-zinc-950 text-white font-sans selection:bg-red-500/30">
        
        <Sidebar className="border-r border-zinc-900 bg-zinc-950">
          <SidebarHeader className="border-b border-zinc-900 p-4">
            <div className="flex items-center gap-2 font-bold text-white">
              <div className="flex h-8 w-8 items-center justify-center rounded bg-red-700 text-white">
                <Factory className="h-5 w-5" />
              </div>
              <span className="truncate">WMS Ops</span>
            </div>
          </SidebarHeader>

          <SidebarContent className="p-2">
            {/* WAREHOUSE PICKER */}
            <div className="mb-6 px-2">
              <label className="text-[10px] uppercase text-zinc-500 font-bold mb-1.5 block">Facility</label>
              {warehouses.length > 0 ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="w-full justify-between bg-zinc-900 border-zinc-800 text-zinc-300 hover:text-white h-9 px-2 text-xs">
                      <div className="flex items-center gap-2 truncate">
                        <Factory className="h-3 w-3 text-red-500" />
                        <span className="truncate">{activeWarehouse?.name}</span>
                      </div>
                      <ChevronsUpDown className="h-3 w-3 opacity-50" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56 bg-zinc-900 border-zinc-800 text-white">
                    {warehouses.map((w) => (
                      <DropdownMenuItem key={w.id} onClick={() => handleSwitch(w)} className="cursor-pointer focus:bg-zinc-800 focus:text-white">
                        <span className="text-xs">{w.name}</span>
                        {activeWarehouse?.id === w.id && <Check className="h-3 w-3 text-red-500 ml-auto" />}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <div className="text-xs text-red-400 border border-red-900/30 p-2 rounded bg-red-950/10">No Warehouse Assigned</div>
              )}
            </div>

            <SidebarGroup>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={location.pathname === "/warehouse-manager"} className="hover:bg-zinc-900 text-zinc-400 data-[active=true]:text-white data-[active=true]:bg-zinc-900">
                      <Link to="/warehouse-manager"><LayoutDashboard className="h-4 w-4" /> <span>Overview</span></Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={location.pathname.includes("/inventory")} className="hover:bg-zinc-900 text-zinc-400 data-[active=true]:text-white data-[active=true]:bg-zinc-900">
                      <Link to="/warehouse-manager/inventory"><PackageSearch className="h-4 w-4" /> <span>Inventory</span></Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={location.pathname.includes("/outbound")} className="hover:bg-zinc-900 text-zinc-400 data-[active=true]:text-white data-[active=true]:bg-zinc-900">
                      <Link to="/warehouse-manager/outbound"><Truck className="h-4 w-4" /> <span>Outbound</span></Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="border-t border-zinc-900 p-2 bg-zinc-950">
            <SidebarMenuButton onClick={handleLogout} className="text-zinc-500 hover:text-red-400 hover:bg-red-950/10">
              <LogOut className="h-4 w-4 mr-2" /> Sign Out
            </SidebarMenuButton>
          </SidebarFooter>
        </Sidebar>

        <main className="flex-1 flex flex-col min-w-0">
          <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b border-zinc-900 bg-zinc-950/80 px-4 backdrop-blur-md">
            <SidebarTrigger className="-ml-1 text-zinc-400 hover:text-white" />
            <Separator orientation="vertical" className="mr-2 h-4 bg-zinc-800" />
            <span className="text-sm font-medium text-zinc-300">Warehouse Operations</span>
          </header>

          <div className="flex-1 overflow-auto p-6">
             {activeWarehouse ? <Outlet context={{ warehouseId: activeWarehouse.id }} /> : (
                 <div className="h-full flex flex-col items-center justify-center text-zinc-600">
                    <AlertTriangle className="h-12 w-12 mb-4 opacity-20" />
                    <p>Select a facility to proceed.</p>
                 </div>
             )}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}