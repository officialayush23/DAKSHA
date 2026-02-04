import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';

export default function AdminLayout() {
  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      
      {/* Sidebar - Fixed on the left */}
      <Sidebar className="hidden border-r bg-background md:block" />

      {/* Main Content Area */}
      <div className="flex flex-col">
        <Header />
        
        {/* REMOVED: 'p-4', 'lg:p-6', 'bg-muted/10'
           This removes the "gap" and the gray box background.
           Now the content will be flush against the edges.
        */}
        <main className="flex flex-1 flex-col">
          <div className="p-4 lg:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}