import React from "react";
import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { 
  LifeBuoy, LayoutDashboard, Inbox, History, LogOut, UserCircle
} from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarHeader, SidebarFooter, SidebarProvider, SidebarTrigger
} from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { supabase } from "@/lib/supabaseClient";

export default function SupportLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    window.location.href = "/login";
  };

  const menuItems = [
    { title: "Dashboard", url: "/support-agent", icon: LayoutDashboard },
    { title: "Ticket Inbox", url: "/support-agent/tickets", icon: Inbox },
    { title: "Resolved History", url: "/support-agent/history", icon: History },
  ];

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-black text-white font-sans selection:bg-indigo-500/30">
        
        {/* SIDEBAR */}
        <Sidebar collapsible="icon" className="border-r border-zinc-800 bg-black">
          <SidebarHeader className="border-b border-zinc-900 bg-black p-4">
            <div className="flex items-center gap-2 font-bold text-white">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
                <LifeBuoy className="h-5 w-5" />
              </div>
              <span className="truncate">Support Desk</span>
            </div>
          </SidebarHeader>
          
          <SidebarContent className="bg-black">
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  {menuItems.map((item) => {
                    const isActive = location.pathname === item.url;
                    return (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton 
                          asChild 
                          isActive={isActive}
                          className="text-zinc-400 hover:text-white hover:bg-zinc-900 data-[active=true]:bg-zinc-800 data-[active=true]:text-white h-10 transition-colors"
                        >
                          <Link to={item.url}>
                            <item.icon className="h-4 w-4" />
                            <span>{item.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    );
                  })}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="bg-black border-t border-zinc-900 p-2">
            <SidebarMenu>
              <SidebarMenuItem>
                <div className="flex items-center gap-3 px-2 py-3 mb-2">
                   <UserCircle className="h-8 w-8 text-zinc-600" />
                   <div className="flex flex-col overflow-hidden">
                      <span className="text-sm font-medium text-white truncate">Agent</span>
                      <span className="text-xs text-zinc-500 truncate">Online</span>
                   </div>
                </div>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton onClick={handleLogout} className="text-red-400 hover:text-red-300 hover:bg-red-950/20 group">
                  <LogOut className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  <span>Logout</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarFooter>
        </Sidebar>

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out">
          <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-2 border-b border-zinc-900 bg-black/80 px-4 backdrop-blur-md">
            <SidebarTrigger className="-ml-1 text-zinc-400 hover:text-white" />
            <Separator orientation="vertical" className="mr-2 h-4 bg-zinc-800" />
            <span className="text-sm font-medium text-zinc-300">Customer Support Console</span>
          </header>

          <div className="flex-1 w-full bg-black p-6 overflow-hidden">
            <Outlet />
          </div>
        </main>

      </div>
    </SidebarProvider>
  );
}