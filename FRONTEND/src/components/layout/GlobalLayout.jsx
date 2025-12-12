import React from "react";
import { Outlet } from "react-router-dom";
import { Bot, MessageSquareText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";

export function GlobalLayout() {
  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      {/* This renders the current page (Dashboard, Orders, etc.) */}
      <Outlet />

      {/* --- PERSISTENT AI AGENT BUTTON --- */}
      <div className="fixed bottom-6 right-6 z-50">
        <Sheet>
          <SheetTrigger asChild>
            <Button 
              className="h-14 w-14 rounded-full shadow-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 hover:scale-110"
            >
              <Bot className="h-7 w-7 text-white" />
              <span className="sr-only">Open AI Assistant</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-full sm:w-[400px] flex flex-col p-0">
            <SheetHeader className="px-6 py-4 border-b bg-muted/40">
              <SheetTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-purple-600" />
                Daksha AI Agent
              </SheetTitle>
            </SheetHeader>
            
            {/* Chat Area Placeholder */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center">
                   <Bot className="h-5 w-5 text-purple-600" />
                </div>
                <div className="bg-muted p-3 rounded-lg rounded-tl-none text-sm max-w-[80%]">
                  Hello! I can help you check inventory, find products, or track your orders. How can I help today?
                </div>
              </div>
            </div>

            {/* Input Area */}
            <div className="p-4 border-t">
               <div className="relative">
                 <input 
                   className="w-full bg-muted/50 border rounded-full pl-4 pr-10 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                   placeholder="Type a message..."
                 />
                 <Button size="icon" variant="ghost" className="absolute right-1 top-1 h-8 w-8 rounded-full">
                   <MessageSquareText className="h-4 w-4 text-muted-foreground" />
                 </Button>
               </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}