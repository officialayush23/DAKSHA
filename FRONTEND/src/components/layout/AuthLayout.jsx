// src/components/layout/AuthLayout.jsx
import React from "react";
import { ModeToggle } from "@/components/use_ui/ModeToggle";

export function AuthLayout({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="flex items-center justify-between px-6 py-4 border-b">
        <div className="font-semibold tracking-tight uppercase text-sm">
          Daksha Retail
        </div>
        <ModeToggle />
      </header>

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-md">{children}</div>
      </main>
    </div>
  );
}
