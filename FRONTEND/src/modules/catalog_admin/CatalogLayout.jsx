import React, { useEffect, useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { 
  Bell, Search, User, Command, Loader2, ShieldAlert
} from "lucide-react";
import api from "@/lib/apiClient"; 
import { supabase } from "@/lib/supabaseClient"; // Import Supabase directly for Role Check
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import CatalogSidebar from "./components/CatalogSidebar";

export default function CatalogLayout() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [userProfile, setUserProfile] = useState(null);

  useEffect(() => {
    const checkCatalogAccess = async () => {
      try {
        setLoading(true);

        // 1. Get Current User ID (from Backend Session or Supabase Auth)
        const { data: { user } } = await supabase.auth.getUser();
        
        if (!user) {
           navigate("/login", { replace: true });
           return;
        }

        // 2. Check 'user_roles' table for 'catalog_admin'
        // This matches the new Backend Logic exactly
        const { data: roles, error } = await supabase
          .from("user_roles")
          .select("role")
          .eq("user_id", user.id);

        if (error) throw error;

        // Flatten roles to simple array: ['store_manager', 'catalog_admin']
        const myRoles = roles.map(r => r.role);
        console.log("My Roles:", myRoles);

        if (myRoles.includes("catalog_admin") || myRoles.includes("super_admin")) {
           setIsAuthorized(true);
           // Optional: Get full profile details for the UI header
           const profile = await api.get("/users/me"); 
           setUserProfile(profile.data);
        } else {
           console.warn("⛔ Access Denied: User is " + myRoles.join(", "));
           navigate("/unauthorized", { replace: true });
        }

      } catch (err) {
        console.error("Auth Check Error:", err);
        navigate("/login");
      } finally {
        setLoading(false);
      }
    };

    checkCatalogAccess();
  }, []);

  if (loading) {
     return (
        <div className="h-screen w-full bg-black flex items-center justify-center text-white">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
     );
  }

  if (!isAuthorized) return null;

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-black text-white font-sans">
        
        {/* Pass role to sidebar if it needs to hide/show links */}
        <CatalogSidebar userRole="catalog_admin" />
        
        <main className="flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out">
          
          <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center justify-between gap-2 border-b border-zinc-800 bg-black/80 px-4 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <SidebarTrigger className="-ml-1 text-zinc-400 hover:text-white" />
              <Separator orientation="vertical" className="mr-2 h-4 bg-zinc-800" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="/catalog" className="text-xs font-medium text-zinc-500 hover:text-zinc-300">Catalog</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block text-zinc-700" />
                  <BreadcrumbItem>
                    <BreadcrumbPage className="text-xs font-medium text-zinc-200">Manager</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-400 hover:text-white hover:bg-zinc-900">
                  <Bell className="h-4 w-4" />
                </Button>
                <div className="h-8 w-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center ml-2">
                  <User className="h-4 w-4 text-zinc-400" />
                </div>
              </div>
            </div>
          </header>

          <div className="flex-1 w-full bg-black p-6">
            <Outlet context={{ admin: userProfile }} />
          </div>
          
        </main>
      </div>
    </SidebarProvider>
  );
}