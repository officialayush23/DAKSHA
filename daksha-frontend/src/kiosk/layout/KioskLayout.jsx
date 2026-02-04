import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import { LogOut, ShoppingBag, Home } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function KioskLayout() {
  const { resetIdleTimer, sessionActive, endSession, cartCount } = useKiosk();
  const navigate = useNavigate();

  return (
    // The outer div captures ALL touches to reset the inactivity timer
    <div 
      className="min-h-screen bg-slate-50 touch-manipulation select-none" 
      onClick={resetIdleTimer}
      onTouchStart={resetIdleTimer}
    >
      {/* Header - Only visible when session is active (not on Attract/Login screen usually) */}
      {sessionActive && (
        <header className="bg-white border-b h-20 px-6 flex items-center justify-between shadow-sm sticky top-0 z-50">
          
          {/* Left: Brand or Home */}
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              size="lg" 
              className="h-12 w-12 p-0 rounded-full"
              onClick={() => navigate('/kiosk/catalog')}
            >
              <Home className="w-8 h-8 text-primary" />
            </Button>
            <div className="font-bold text-2xl tracking-tight hidden md:block text-primary">
              DAKSHA <span className="font-normal text-muted-foreground">Kiosk</span>
            </div>
          </div>
          
          {/* Right: Actions */}
          <div className="flex items-center gap-4">
            <Button 
              variant="outline" 
              size="lg" 
              className="h-12 px-6 text-lg gap-2 relative"
              onClick={() => navigate('/kiosk/checkout')}
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
      )}

      {/* Main Content Area */}
      <main className="w-full h-full">
        <Outlet />
      </main>
    </div>
  );
}