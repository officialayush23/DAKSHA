import React, { useState, useEffect } from "react";
import { Outlet, useOutletContext, useNavigate, useLocation } from "react-router-dom";
import api from "@/lib/apiClient"; 
import { 
  Bell, User, MapPin, Store, ChevronsUpDown, Check, Loader2, AlertCircle 
} from "lucide-react";

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import StoreSidebar from "./components/StoreSidebar";

export default function StoreLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  
  // 1. Get Context (might be null if login flow is skipped/buggy)
  const roleData = useOutletContext() || {}; 

  const [activeStore, setActiveStore] = useState(null);
  const [storeList, setStoreList] = useState([]);
  const [loading, setLoading] = useState(true);

  // Dynamic Breadcrumb
  const pathSegments = location.pathname.split("/").filter(Boolean);
  const currentPage = pathSegments.length > 1 
    ? pathSegments[1].replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase())
    : "Dashboard";

  useEffect(() => {
    const fetchStores = async () => {
      console.log("🚀 Attempting to fetch stores with current Token...");
      setLoading(true);

      try {
        // 2. We call API immediately. 
        // We DON'T wait for user_id. The Backend extracts it from the Token.
        const res = await api.get("/users/me/stores");
        
        console.log("📦 Stores Loaded:", res.data);

        if (res.data && Array.isArray(res.data) && res.data.length > 0) {
          setStoreList(res.data);

          // 3. Logic: Try to match the store from Context, otherwise pick the first one
          const preferredId = roleData?.store_id;
          const matched = res.data.find(s => s.id === preferredId) || res.data[0];
          
          setActiveStore(matched);
        } else {
            console.warn("⚠️ API returned no stores (Empty Array)");
        }
      } catch (err) {
        console.error("❌ API Call Failed:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStores();
  }, []); // Run ONCE on mount, regardless of context

  const handleSwitchStore = (store) => {
    setActiveStore(store);
    navigate("/store-manager");
  };

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-black text-white font-sans selection:bg-emerald-500/30">
        
        <StoreSidebar />
        
        <main className="flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out">
          
          <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between gap-2 border-b border-zinc-900 bg-black/80 px-4 backdrop-blur-md">
            
            <div className="flex items-center gap-2">
              <SidebarTrigger className="-ml-1 text-zinc-400 hover:text-white" />
              <Separator orientation="vertical" className="mr-2 h-4 bg-zinc-800" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="/store-manager" className="text-xs font-medium text-zinc-500 hover:text-zinc-300">
                      Operations
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block text-zinc-700" />
                  <BreadcrumbItem>
                    <BreadcrumbPage className="text-xs font-medium text-zinc-200">
                      {currentPage}
                    </BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>

            <div className="flex items-center gap-4">
              
              {/* STORE SWITCHER */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="outline" 
                    className="hidden md:flex items-center gap-2 bg-zinc-900/50 border-zinc-800 px-3 py-1 h-8 rounded-full transition-all hover:bg-zinc-900 hover:border-zinc-700 hover:text-white"
                  >
                    <MapPin className="h-3 w-3 text-emerald-500" />
                    
                    {loading ? (
                       <span className="text-xs text-zinc-500 flex items-center gap-1">
                         <Loader2 className="h-3 w-3 animate-spin"/> Loading...
                       </span>
                    ) : (
                       <span className="text-xs font-medium text-zinc-300 truncate max-w-[150px]">
                         {activeStore ? activeStore.name : "Select Store"}
                       </span>
                    )}

                    <ChevronsUpDown className="ml-1 h-3 w-3 text-zinc-500" />
                  </Button>
                </DropdownMenuTrigger>

                <DropdownMenuContent className="w-[220px] bg-zinc-950 border-zinc-800 text-white">
                  <DropdownMenuLabel className="text-xs text-zinc-500">My Locations</DropdownMenuLabel>
                  <DropdownMenuSeparator className="bg-zinc-800" />
                  
                  {storeList.length === 0 && !loading ? (
                    <div className="p-2 text-xs text-zinc-500 text-center flex flex-col items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      No stores assigned
                    </div>
                  ) : (
                    storeList.map((store) => (
                      <DropdownMenuItem
                        key={store.id}
                        onClick={() => handleSwitchStore(store)}
                        className="text-sm focus:bg-zinc-900 focus:text-white cursor-pointer"
                      >
                        <Store className="mr-2 h-4 w-4 text-zinc-400" />
                        <div className="flex flex-col">
                            <span className="truncate font-medium">{store.name}</span>
                            <span className="text-[10px] text-zinc-500">{store.city}</span>
                        </div>
                        {activeStore?.id === store.id && <Check className="ml-auto h-4 w-4 text-emerald-500" />}
                      </DropdownMenuItem>
                    ))
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded-full">
                  <Bell className="h-4 w-4" />
                </Button>
                <div className="h-8 w-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center ml-2">
                  <User className="h-4 w-4 text-zinc-400" />
                </div>
              </div>
            </div>
          </header>

          <div className="flex-1 w-full bg-black p-6">
            {/* CRITICAL: We merge roleData + activeStore. 
               This ensures the Dashboard gets the ID even if roleData is empty.
            */}
            <Outlet context={{ 
                ...roleData, 
                store_id: activeStore?.id,
                store_name: activeStore?.name,
                store_code: activeStore?.code
            }} />
          </div>
          
        </main>
      </div>
    </SidebarProvider>
  );
}