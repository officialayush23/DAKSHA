import React from "react";
import { Link, useLocation } from "react-router-dom";
import { 
  LayoutDashboard, 
  PackageSearch, 
  ShoppingCart, 
  Settings, 
  Store 
} from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar";

// Menu items for the Inventory Panel
const items = [
  {
    title: "Store Dashboard",
    url: "/inventory",
    icon: LayoutDashboard,
  },
  {
    title: "Stock Control",
    url: "/inventory/stock",
    icon: PackageSearch,
  },
  {
    title: "Incoming Orders",
    url: "/inventory/orders",
    icon: ShoppingCart,
  },
  {
    title: "Settings",
    url: "/inventory/settings",
    icon: Settings,
  },
];

export default function InventorySidebar() {
  const location = useLocation();

  return (
    <Sidebar>
      <SidebarHeader className="border-b p-4">
        <div className="flex items-center gap-2 font-semibold">
          <Store className="h-6 w-6" />
          <span className="">Store Ops</span>
        </div>
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Management</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild 
                    isActive={location.pathname === item.url}
                    tooltip={item.title}
                  >
                    <Link to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
