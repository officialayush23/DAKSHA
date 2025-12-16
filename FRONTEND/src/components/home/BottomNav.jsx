// src/components/home/BottomNav.jsx

import { Home, Search, ShoppingCart, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";

export default function BottomNav() {
  const nav = useNavigate();
  const { pathname } = useLocation();

  const Item = ({ icon: Icon, label, to }) => (
    <Button
      variant="ghost"
      className={`flex flex-col gap-1 h-auto ${
        pathname === to ? "text-white" : "text-muted-foreground"
      }`}
      onClick={() => nav(to)}
    >
      <Icon className="h-5 w-5" />
      <span className="text-[10px]">{label}</span>
    </Button>
  );

  return (
    <div className="fixed bottom-0 left-0 right-0 md:hidden border-t bg-background backdrop-blur">
      <div className="flex justify-around py-2">
        <Item icon={Home} label="Home" to="/home" />
        <Item icon={Search} label="Search" to="/products" />
        <Item icon={ShoppingCart} label="Cart" to="/cart" />
        <Item icon={User} label="Profile" to="/profile" />
      </div>
    </div>
  );
}
