// daksha-frontend/src/admin_user/AdminUserLayout.jsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import UserList from './pages/Users';

export default function AdminUserLayout() {
  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-80px)] overflow-hidden">
      {/* LEFT SIDE: The User Table/Search */}
      <div className="flex-1 min-w-0 bg-background rounded-xl border shadow-sm overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4">
          <UserList hideDetailView={true} /> 
        </div>
      </div>

      {/* RIGHT SIDE: The Detail Profile (Scrollable) */}
      <div className="w-full lg:w-[450px] xl:w-[550px] overflow-y-auto pr-2">
        <Outlet />
      </div>
    </div>
  );
}