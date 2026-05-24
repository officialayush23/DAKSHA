import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingBag, Home, LogOut, Sparkles, LayoutGrid } from 'lucide-react';

export default function KioskHeader() {
  const navigate  = useNavigate();
  const location  = useLocation();
  const { cartCount, endSession, user } = useKiosk();

  const isChat    = location.pathname === '/kiosk/chat';
  const isCatalog = location.pathname === '/kiosk/shop';

  return (
    <header className="bg-white border-b h-20 px-6 flex items-center justify-between shadow-sm sticky top-0 z-50">

      {/* ── Left: Brand + Home ─── */}
      <div className="flex items-center gap-3 min-w-[180px]">
        <Button
          type="button"
          variant="ghost"
          size="lg"
          className="h-12 w-12 p-0 rounded-full"
          onClick={() => navigate('/kiosk/chat')}
        >
          <Home className="w-7 h-7 text-slate-600" />
        </Button>
        <div className="font-bold text-xl tracking-tight text-slate-900 hidden md:block">
          DAKSHA <span className="font-light text-slate-400 text-base">Kiosk</span>
        </div>
      </div>

      {/* ── Center: Primary navigation ─── */}
      <div className="flex items-center gap-3">

        {/* Agent — primary CTA, always prominent */}
        <button
          type="button"
          onClick={() => navigate('/kiosk/chat')}
          className={`
            flex items-center gap-2.5 px-7 py-3 rounded-2xl text-base font-semibold transition-all
            ${isChat
              ? 'bg-slate-900 text-white shadow-lg scale-105'
              : 'bg-slate-900 text-white hover:bg-slate-700 shadow-md hover:scale-105'}
          `}
        >
          <Sparkles className="w-5 h-5" />
          Ask Daksha AI
        </button>

        {/* Catalog — secondary */}
        <button
          type="button"
          onClick={() => navigate('/kiosk/shop')}
          className={`
            flex items-center gap-2.5 px-6 py-3 rounded-2xl text-base font-medium transition-all border-2
            ${isCatalog
              ? 'bg-slate-100 border-slate-300 text-slate-900'
              : 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300'}
          `}
        >
          <LayoutGrid className="w-5 h-5" />
          Browse
        </button>
      </div>

      {/* ── Right: User greeting + Cart + Exit ─── */}
      <div className="flex items-center gap-3 min-w-[180px] justify-end">
        {user && (
          <span className="hidden lg:block text-slate-500 text-sm font-medium truncate max-w-[100px]">
            {user.name}
          </span>
        )}

        {/* Cart */}
        <button
          type="button"
          onClick={() => navigate('/kiosk/cart')}
          className="relative flex items-center gap-2 h-12 px-5 rounded-2xl border-2 border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors text-base font-medium"
        >
          <ShoppingBag className="w-5 h-5" />
          <span className="hidden sm:inline">Cart</span>
          {cartCount > 0 && (
            <span className="absolute -top-2 -right-2 h-6 w-6 bg-slate-900 text-white text-xs font-bold rounded-full flex items-center justify-center">
              {cartCount > 9 ? '9+' : cartCount}
            </span>
          )}
        </button>

        {/* Exit */}
        <button
          type="button"
          onClick={() => endSession("Session ended")}
          className="flex items-center gap-2 h-12 px-5 rounded-2xl bg-red-50 text-red-500 hover:bg-red-100 transition-colors text-base font-medium border-2 border-red-100"
        >
          <LogOut className="w-5 h-5" />
          <span className="hidden sm:inline">Exit</span>
        </button>
      </div>
    </header>
  );
}
