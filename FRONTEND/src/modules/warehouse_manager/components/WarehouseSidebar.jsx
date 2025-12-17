// import React from "react";
// import { Link, useLocation } from "react-router-dom";
// import { 
//   LayoutDashboard, Package, Truck, ClipboardList, LogOut 
// } from "lucide-react";
// import {
//   Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarHeader, SidebarFooter
// } from "@/components/ui/sidebar";
// import { supabase } from "@/lib/supabaseClient";

// export default function WarehouseSidebar() {
//   const location = useLocation();

//   const handleLogout = async () => {
//     await supabase.auth.signOut();
//     window.location.href = "/login";
//   };

//   const menuItems = [
//     { title: "Dashboard", url: "/warehouse-manager", icon: LayoutDashboard },
//     { title: "Inventory", url: "/warehouse-manager/inventory", icon: Package },
//     { title: "Inbound", url: "/warehouse-manager/inbound", icon: ClipboardList },
//     { title: "Outbound", url: "/warehouse-manager/outbound", icon: Truck },
//   ];

//   return (
//     <Sidebar collapsible="icon" className="border-r border-zinc-800 bg-black">
//       <SidebarHeader className="border-b border-zinc-900 bg-black p-4">
//         <div className="flex items-center gap-2 font-bold text-white">
//           <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-600 text-white">
//             W
//           </div>
//           <span className="truncate">Warehouse</span>
//         </div>
//       </SidebarHeader>
      
//       <SidebarContent className="bg-black">
//         <SidebarGroup>
//           <SidebarGroupContent>
//             <SidebarMenu>
//               {menuItems.map((item) => (
//                 <SidebarMenuItem key={item.title}>
//                   <SidebarMenuButton asChild isActive={location.pathname === item.url} className="text-zinc-400 hover:text-white hover:bg-zinc-900 data-[active=true]:bg-zinc-800 data-[active=true]:text-white">
//                     <Link to={item.url}>
//                       <item.icon />
//                       <span>{item.title}</span>
//                     </Link>
//                   </SidebarMenuButton>
//                 </SidebarMenuItem>
//               ))}
//             </SidebarMenu>
//           </SidebarGroupContent>
//         </SidebarGroup>
//       </SidebarContent>

//       <SidebarFooter className="bg-black border-t border-zinc-900 p-2">
//         <SidebarMenu>
//           <SidebarMenuItem>
//             <SidebarMenuButton onClick={handleLogout} className="text-red-400 hover:text-red-300 hover:bg-red-950/20">
//               <LogOut />
//               <span>Logout</span>
//             </SidebarMenuButton>
//           </SidebarMenuItem>
//         </SidebarMenu>
//       </SidebarFooter>
//     </Sidebar>
//   );
// }