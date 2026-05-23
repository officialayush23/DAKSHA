import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Touchpad } from 'lucide-react';

export default function AttractScreen() {
  const navigate = useNavigate();

  return (
    <div 
      className="h-screen w-full bg-slate-900 relative overflow-hidden cursor-pointer"
      onClick={() => navigate('/kiosk/login')}
    >
      {/* Background */}
      <div className="absolute inset-0 opacity-40">
        <img 
          src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=2070&auto=format&fit=crop" 
          alt="Store Background" 
          className="w-full h-full object-cover"
        />
      </div>

      {/* Content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center text-white space-y-8">
        <div className="text-center space-y-4 animate-pulse">
          <h1 className="text-6xl font-extrabold tracking-tighter">
            Welcome to DAKSHA
          </h1>
          <p className="text-2xl text-slate-200 font-light">
            Experience the Future of Retail
          </p>
        </div>
        <div className="mt-12">
          <Button 
            size="lg" 
            className="h-20 px-12 text-2xl rounded-full bg-white text-slate-900 hover:bg-slate-200 hover:scale-105 transition-all duration-300 shadow-2xl border-none"
          >
            <Touchpad className="w-8 h-8 mr-3" />
            Touch to Start
          </Button>
        </div>
      </div>

      <div className="absolute bottom-8 w-full text-center text-slate-400 text-sm">
        Daksha Kiosk • Version 1.0.0
      </div>
    </div>
  );
}
