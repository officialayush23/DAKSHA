import * as React from "react"
import { Link, useLocation } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { useQuery } from "@tanstack/react-query"
import { apiRequest } from "../lib/api"
import {
  ShoppingBag,
  ShoppingCart,
  Package,
  Sparkles,
  LayoutDashboard,
  LogOut,
  User,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarGroup,
  SidebarGroupContent,
} from "./ui/sidebar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu"
import { Avatar, AvatarFallback } from "./ui/avatar"

export function AppSidebar({ ...props }) {
  const { user, signOut, profile } = useAuth()
  const location = useLocation()
  
  const { data: cart } = useQuery({
    queryKey: ['cart'],
    queryFn: () => apiRequest('/cart/'),
    refetchInterval: 5000, 
  })
  
  const cartCount = cart?.items?.reduce((acc, item) => acc + item.quantity, 0) || 0
  const isAdmin = profile?.role === 'admin' || user?.app_metadata?.role === 'admin'

  const navItems = [
    { title: "Shop", url: "/demo/products", icon: ShoppingBag },
    { title: "Agent", url: "/demo/chat", icon: Sparkles },
    { title: "Cart", url: "/demo/cart", icon: ShoppingCart, badge: cartCount },
    { title: "Orders", url: "/demo/orders", icon: Package },
    { title: "Profile", url: "/demo/profile", icon: User },
  ]

  if (isAdmin) {
    navItems.push({ title: "Admin", url: "/demo/admin", icon: LayoutDashboard })
  }

  return (
    <Sidebar className="border-r border-zinc-100 bg-white" {...props}>
      <SidebarHeader className="p-8 pb-6">
        <Link to="/" className="flex items-center gap-2 px-2">
           {/* Pure Text Logo - Charm Font */}
           <h1 className="text-5xl font-bold font-charm text-black tracking-tight hover:opacity-80 transition-opacity">
             Weeb
           </h1>
        </Link>
      </SidebarHeader>

      <SidebarContent className="px-4 py-4">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-2">
              {navItems.map((item) => {
                 const isActive = location.pathname.startsWith(item.url)
                 return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton 
                        asChild 
                        size="lg"
                        className={`
                            h-12 rounded-full transition-all duration-300 px-5 group
                            ${isActive 
                                ? 'bg-black text-white shadow-lg shadow-black/10 hover:bg-black hover:text-white' 
                                : 'text-zinc-500 hover:bg-zinc-50 hover:text-black'
                            }
                        `}
                    >
                      <Link to={item.url} className="flex items-center gap-4">
                        <item.icon 
                            size={20} 
                            strokeWidth={isActive ? 2.5 : 2} 
                            className={isActive ? "text-white" : "text-zinc-400 group-hover:text-black"}
                        />
                        <span className="font-medium text-sm tracking-wide">{item.title}</span>
                        
                        {item.badge > 0 && (
                            <span className={`
                                ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full
                                ${isActive ? 'bg-white text-black' : 'bg-zinc-100 text-black'}
                            `}>
                                {item.badge}
                            </span>
                        )}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                 )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-6">
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-3 p-2 rounded-xl hover:bg-zinc-50 transition-colors w-full group outline-none">
                <Avatar className="h-10 w-10 rounded-full border border-zinc-100 group-hover:border-zinc-300 transition-colors">
                    <AvatarFallback className="bg-zinc-50 text-zinc-900 font-bold">
                        {user?.email?.[0].toUpperCase()}
                    </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left">
                    <span className="truncate text-sm font-semibold text-zinc-900">{user?.user_metadata?.full_name || 'Member'}</span>
                    <span className="truncate text-xs text-zinc-400">{user?.email}</span>
                </div>
            </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 rounded-2xl p-2 shadow-xl border-zinc-100" side="top" align="center">
                <DropdownMenuItem onClick={signOut} className="text-red-600 focus:text-red-600 focus:bg-red-50 rounded-lg cursor-pointer p-3 font-medium">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
      </SidebarFooter>
    </Sidebar>
  )
}