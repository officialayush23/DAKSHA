import React from 'react';
import { Outlet } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import KioskHeader from '../components/KioskHeader';

export default function KioskLayout() {
  const { resetIdleTimer } = useKiosk();

  return (
    <div
      className="min-h-screen bg-slate-50 touch-manipulation select-none"
      onClick={resetIdleTimer}
      onTouchStart={resetIdleTimer}
    >
      {/* Header — always shown, route guard ensures session is active */}
      <KioskHeader />

      {/* Main Content Area */}
      <main className="w-full h-full">
        <Outlet />
      </main>
    </div>
  );
}