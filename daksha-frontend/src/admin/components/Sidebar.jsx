import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { supabase } from '@/lib/supabaseClient';
import { 
  LayoutDashboard, 
  Package, 
  Store, 
  ShoppingCart, 
  Users, 
  AlertCircle, 
  Tag, 
  LogOut,Monitor,
  LucideLandmark,
  ShieldCheck
} from 'lucide-react';
import { Button } from "../../components/ui/button";
import { cn } from "@/lib/utils";

// Helper component for consistent links
const SidebarItem = ({ to, icon: Icon, label, onClick }) => (
  <NavLink
    to={to}
    onClick={onClick}
    className={({ isActive }) =>
      cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 transition-all hover:text-primary",
        isActive 
          ? "bg-muted text-primary font-medium" 
          : "text-muted-foreground"
      )
    }
  >
    <Icon className="h-4 w-4" />
    {label}
  </NavLink>
);

export default function Sidebar({ className, onLinkClick }) {
  const navigate = useNavigate();

  // --- Logout Logic ---
  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
      navigate('/login');
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <div className={cn("flex h-full max-h-screen flex-col gap-2", className)}>
      {/* Branding / Logo */}
      <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
        <NavLink to="/admin/dashboard" className="flex items-center gap-2 font-bold text-lg">
          <span className="text-primary">DAKSHA</span>
          <span className="text-muted-foreground font-normal">Admin</span>
        </NavLink>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-auto py-2">
        <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
          <SidebarItem to="/admin/dashboard" icon={LayoutDashboard} label="Dashboard" onClick={onLinkClick} />
          <SidebarItem to="/admin/products" icon={Package} label="Products" onClick={onLinkClick} />
          <SidebarItem to="/admin/stores" icon={Store} label="Stores" onClick={onLinkClick} />
          <SidebarItem to="/admin/orders" icon={ShoppingCart} label="Orders" onClick={onLinkClick} />
          <SidebarItem to="/admin/offers" icon={Tag} label="Offers" onClick={onLinkClick} />
          <SidebarItem to="/admin/complaints" icon={AlertCircle} label="Complaints" onClick={onLinkClick} />
          <SidebarItem to="/admin/handoffs" icon={Users} label="Agent Handoffs" onClick={onLinkClick} />
          <SidebarItem to="/admin/returns" icon={Users} label="Returns" onClick={onLinkClick} />
          <SidebarItem to="/admin/kiosks" icon={Monitor} label="Kiosks" onClick={onLinkClick} />
          <SidebarItem to="/admin/discount-rules" icon={Tag} label="Discount Rules" onClick={onLinkClick} />
          <SidebarItem to="/admin/agent-runs" icon={LucideLandmark} label="Agent Runs" onClick={onLinkClick} />
          <SidebarItem to="/admin/users" icon={ShieldCheck} label="Admin Users" onClick={onLinkClick}/>
          <SidebarItem to="/admin/payment-manage" icon={Tag} label="Payment Management" onClick={onLinkClick} />
        </nav>
      </div>

      {/* Footer / Logout */}
      <div className="mt-auto p-4 border-t">
        <Button 
          variant="outline" 
          className="w-full gap-2 justify-start hover:text-red-600 hover:bg-red-50"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" /> 
          Logout
        </Button>
      </div>
    </div>
  );
}