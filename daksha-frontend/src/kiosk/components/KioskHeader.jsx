import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingBag, Home, LogOut } from 'lucide-react';

export default function KioskHeader() {
  const navigate = useNavigate();
  const { cartCount, endSession, user } = useKiosk();

  return (
    <header className="bg-white border-b h-20 px-6 flex items-center justify-between shadow-sm sticky top-0 z-50">

      {/* Left: Brand + Home */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="lg"
          className="h-12 w-12 p-0 rounded-full"
          onClick={() => navigate('/kiosk/shop')}
        >
          <Home className="w-8 h-8 text-primary" />
        </Button>
        <div className="font-bold text-2xl tracking-tight hidden md:block text-primary">
          DAKSHA <span className="font-normal text-muted-foreground">Kiosk</span>
        </div>
      </div>

      {/* Center: User greeting if logged in */}
      {user && (
        <div className="hidden md:flex items-center gap-2 text-slate-600 text-lg">
          <span>Welcome,</span>
          <span className="font-bold text-slate-900">{user.name}</span>
        </div>
      )}

      {/* Right: Cart + Exit */}
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="lg"
          className="h-12 px-6 text-lg gap-2 relative"
          onClick={() => navigate('/kiosk/cart')}
        >
          <ShoppingBag className="w-6 h-6" />
          <span className="hidden sm:inline">Cart</span>
          {cartCount > 0 && (
            <Badge className="absolute -top-2 -right-2 h-6 w-6 flex items-center justify-center rounded-full text-xs">
              {cartCount}
            </Badge>
          )}
        </Button>

        <Button
          variant="destructive"
          size="lg"
          className="h-12 px-6 text-lg gap-2"
          onClick={() => endSession("Session ended by user")}
        >
          <LogOut className="w-6 h-6" />
          <span className="hidden sm:inline">Exit</span>
        </Button>
      </div>
    </header>
  );
}