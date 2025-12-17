// src/components/layout/GlobalLayout.jsx
import React from "react";
import { Outlet } from "react-router-dom";
import { Bot, MessageSquareText, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { motion } from "framer-motion";

export function GlobalLayout() {
  return (
    <div className="min-h-screen bg-background font-sans antialiased selection:bg-cyan-500/30">
      {/* Background Ambient Mesh */}
      <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] opacity-50" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] opacity-50" />
      </div>

      <Outlet />

      {/* --- PERSISTENT AI AGENT BUTTON --- */}
      <div className="fixed bottom-24 md:bottom-8 right-6 z-50">
        <Sheet>
          <SheetTrigger asChild>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button 
                className="h-16 w-16 rounded-full shadow-[0_0_40px_-10px_rgba(6,182,212,0.6)] bg-gradient-to-br from-cyan-400 to-blue-600 hover:from-cyan-300 hover:to-blue-500 border border-white/20 transition-all duration-300"
                >
                <Bot className="h-8 w-8 text-black" />
                <span className="sr-only">Open AI Assistant</span>
                </Button>
            </motion.div>
          </SheetTrigger>
          
          <SheetContent side="right" className="w-full sm:w-[400px] flex flex-col p-0 border-l border-white/10 bg-black/80 backdrop-blur-2xl">
            <SheetHeader className="px-6 py-5 border-b border-white/10 bg-white/5">
              <SheetTitle className="flex items-center gap-2 text-cyan-50">
                <Sparkles className="h-5 w-5 text-cyan-400" />
                <span className="bg-gradient-to-r from-cyan-200 to-blue-200 bg-clip-text text-transparent font-bold">
                    Daksha AI
                </span>
              </SheetTitle>
            </SheetHeader>
            
            {/* Chat Area */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center shrink-0">
                   <Bot className="h-5 w-5 text-cyan-400" />
                </div>
                <div className="bg-white/10 border border-white/5 p-3 rounded-2xl rounded-tl-none text-sm text-gray-200 shadow-lg backdrop-blur-md max-w-[85%]">
                  Hello! I'm your personal stylist. I can help you check inventory, find matching outfits, or track your orders.
                </div>
              </div>
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/10 bg-black/40">
               <div className="relative group">
                 <input 
                   className="w-full bg-white/5 border border-white/10 rounded-full pl-5 pr-12 py-3 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all"
                   placeholder="Ask me anything..."
                 />
                 <Button size="icon" variant="ghost" className="absolute right-1.5 top-1.5 h-9 w-9 rounded-full hover:bg-cyan-500/20">
                   <MessageSquareText className="h-4 w-4 text-cyan-400" />
                 </Button>
               </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}