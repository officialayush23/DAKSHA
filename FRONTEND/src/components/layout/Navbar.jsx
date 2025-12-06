import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { ShoppingCart, User, LogOut, Store } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Navbar() {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav className="border-b bg-background sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl">
          <Store className="h-6 w-6 text-primary" />
          <span>DAKSHA</span>
        </Link>

        <div className="flex items-center gap-6">
          <Link to="/" className="text-sm font-medium hover:text-primary">
            Browse
          </Link>
          <Link to="/orders" className="text-sm font-medium hover:text-primary">
            Orders
          </Link>
          <Link to="/support" className="text-sm font-medium hover:text-primary">
            Support
          </Link>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/cart">
            <Button variant="ghost" size="icon" className="relative">
              <ShoppingCart className="h-5 w-5" />
              <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full" />
            </Button>
          </Link>

          <Link to="/profile">
            <Button variant="ghost" size="icon">
              <User className="h-5 w-5" />
            </Button>
          </Link>

          <Button variant="ghost" size="icon" onClick={handleLogout}>
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </nav>
  );
}