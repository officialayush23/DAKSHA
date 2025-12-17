// FRONTEND/src/components/auth/RoleProtectedRoute.jsx

import React, { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import api from '@/lib/apiClient';
import { useAuth } from '@/context/AuthContext';
import { Skeleton } from "@/components/ui/skeleton";

export default function RoleProtectedRoute({ allowedRoles }) {
  const { user, loading: authLoading } = useAuth();
  const [roleData, setRoleData] = useState(null);
  const [checkingRole, setCheckingRole] = useState(true);
  const [error, setError] = useState(null);
  const location = useLocation();

  useEffect(() => {
    // 1. Wait for Auth Context
    if (authLoading) return;
    
    // 2. If not logged in, stop checking
    if (!user) {
      setCheckingRole(false);
      return;
    }

    const checkRole = async () => {
      try {
        // 3. Call the APIs: get operational roles and user profile
        const [opRes, userRes] = await Promise.all([
          api.get('/users/me/operational-role'),
          api.get('/users/me'),
        ]);

        // Normalize operational roles shape
        const opBody = opRes.data ?? opRes;
        let opRoles = [];
        if (Array.isArray(opBody)) {
          opRoles = opBody.map((r) => r.role || r);
        } else if (Array.isArray(opBody?.operational_roles)) {
          opRoles = opBody.operational_roles.map((r) => r.role || r);
        } else if (opBody?.role) {
          opRoles = [opBody.role];
        }

        // Global role from users table
        const userBody = userRes.data ?? userRes;
        const globalRole = userBody?.role || userBody?.user?.role || null;

        // Combine roles, prefer globalRole as primary if present
        const roles = [...new Set([...(globalRole ? [globalRole] : []), ...opRoles])];
        const primary = globalRole || roles[0] || null;
        setRoleData({ role: primary, roles });
      } catch (err) {
        // Log detailed info for debugging
        console.error('Role check failed:', err?.message || err, 'status=', err?.response?.status, 'data=', err?.response?.data);
        // Map 403/404 to NO_ROLE; other statuses -> API_ERROR
        const status = err?.response?.status;
        if (status === 403 || status === 404) setError('NO_ROLE');
        else setError('API_ERROR');
      } finally {
        setCheckingRole(false);
      }
    };

    checkRole();
  }, [user, authLoading]);

  // --- RENDER STATES ---

  // A. Loading
  if (authLoading || checkingRole) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-black">
        <Skeleton className="h-12 w-12 rounded-full bg-zinc-800" />
      </div>
    );
  }

  // B. Not Logged In
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // C. Error (No Role or API Fail)
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-black text-white p-6 text-center">
        <h1 className="text-xl font-bold text-red-500 mb-2">Access Denied</h1>
        <p className="text-zinc-400">
          {error === "NO_ROLE" 
            ? "Your account is not assigned to any operational role."
            : "System error verifying permissions."}
        </p>
      </div>
    );
  }

  // D. Role Mismatch
  if (roleData && !allowedRoles.includes(roleData.role)) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-black text-white gap-4">
        <h1 className="text-xl font-bold text-amber-500">Restricted Area</h1>
        <p className="text-zinc-400">
          Required: {allowedRoles.join(", ")} <br/>
          Your Role: {roleData.role || (roleData.roles ? roleData.roles.join(', ') : '—')}
        </p>
      </div>
    );
  }

  // E. Success
  return <Outlet context={roleData} />;}