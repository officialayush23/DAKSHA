// src/modules/super_admin/pages/AccessControl.jsx


import React, { useState } from "react";
import api from "@/lib/apiClient"; // Use API Client
import { toast } from "sonner";
import { Loader2, UserCog, Building2, Warehouse, Search, Trash2, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function AccessControl() {
  const [loading, setLoading] = useState(false);
  const [checkLoading, setCheckLoading] = useState(false);
  
  const [form, setForm] = useState({ user_id: "", role: "store_manager", location_id: "" });
  const [lookupUserId, setLookupUserId] = useState("");
  const [userRoles, setUserRoles] = useState([]); 

  // 1. ASSIGN ROLE
  const handleAssign = async (e) => {
    e.preventDefault();
    if(!form.user_id) return toast.error("User ID is required");
    if (form.role !== "super_admin" && !form.location_id) return toast.error("Location ID is required");

    setLoading(true);
    try {
      const payload = {
        user_id: form.user_id.trim(),
        role: form.role,
        store_id: form.role === "store_manager" ? form.location_id : null,
        warehouse_id: form.role === "warehouse_manager" ? form.location_id : null
      };

      await api.post("/admin/super/roles", payload);

      toast.success("Role Assigned Successfully");
      setForm(prev => ({ ...prev, location_id: "" })); 
      if (lookupUserId === form.user_id) handleCheckUser();

    } catch (error) {
      toast.error("Failed to assign role.");
    } finally {
      setLoading(false);
    }
  };

  // 2. CHECK ROLES
  const handleCheckUser = async (e) => {
    if (e) e.preventDefault();
    if (!lookupUserId) return;

    setCheckLoading(true);
    try {
      const res = await api.get(`/admin/super/roles/${lookupUserId.trim()}`);
      setUserRoles(res.data || []);
      if ((res.data || []).length === 0) toast.info("User has no roles assigned.");
    } catch (error) {
      toast.error("Could not fetch user roles.");
      setUserRoles([]); 
    } finally {
      setCheckLoading(false);
    }
  };

  // 3. REVOKE ROLE
  const handleRevoke = async (roleData) => {
    if (!confirm("Revoke access?")) return;

    try {
      await api.post("/admin/super/roles/revoke", {
        user_id: roleData.user_id,
        role: roleData.role,
        store_id: roleData.store_id,
        warehouse_id: roleData.warehouse_id
      });

      toast.success("Access Revoked");
      handleCheckUser(); 

    } catch (error) {
      toast.error("Revoke failed.");
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-5xl mx-auto pb-20">
      
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-bold text-white tracking-tight">Access Control</h2>
        <p className="text-zinc-400">Manage user permissions.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* ASSIGN FORM */}
        <Card className="bg-zinc-950 border-zinc-800 text-white shadow-xl h-fit">
          <CardHeader className="border-b border-zinc-900 pb-6">
            <CardTitle className="text-lg font-medium flex items-center gap-2"><UserCog className="h-5 w-5 text-indigo-500" /> Grant Access</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleAssign} className="space-y-6">
              <div className="space-y-3">
                <Label className="text-zinc-300">User ID (UUID)</Label>
                <Input placeholder="e.g. a0eebc99..." className="bg-zinc-900/50 border-zinc-800" value={form.user_id} onChange={e => setForm({...form, user_id: e.target.value})} />
              </div>
              <div className="space-y-3">
                <Label className="text-zinc-300">Role</Label>
                <Select value={form.role} onValueChange={val => setForm({...form, role: val})}>
                    <SelectTrigger className="bg-zinc-900/50 border-zinc-800"><SelectValue /></SelectTrigger>
                    <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                    <SelectItem value="store_manager">Store Manager</SelectItem>
                    <SelectItem value="warehouse_manager">Warehouse Manager</SelectItem>
                    <SelectItem value="catalog_admin">Catalog Admin</SelectItem>
                    </SelectContent>
                </Select>
              </div>
              {['store_manager', 'warehouse_manager'].includes(form.role) && (
                  <div className="space-y-3">
                    <Label className="text-zinc-300">Location ID</Label>
                    <Input placeholder="Store/Warehouse UUID" className="bg-zinc-900/50 border-zinc-800" value={form.location_id} onChange={e => setForm({...form, location_id: e.target.value})} />
                  </div>
              )}
              <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white" disabled={loading}>
                {loading ? <Loader2 className="animate-spin h-5 w-5" /> : "Confirm Assignment"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* CHECK FORM */}
        <div className="space-y-6">
            <Card className="bg-zinc-950 border-zinc-800 text-white shadow-xl">
                <CardHeader className="border-b border-zinc-900 pb-6">
                    <CardTitle className="text-lg font-medium flex items-center gap-2"><Search className="h-5 w-5 text-emerald-500" /> Verify Access</CardTitle>
                </CardHeader>
                <CardContent className="pt-6 space-y-6">
                    <form onSubmit={handleCheckUser} className="flex gap-3">
                        <Input placeholder="Paste User UUID..." className="bg-zinc-900/50 border-zinc-800" value={lookupUserId} onChange={e => setLookupUserId(e.target.value)} />
                        <Button variant="secondary" className="bg-zinc-800 text-white" disabled={checkLoading}>{checkLoading ? <Loader2 className="animate-spin" /> : "Check"}</Button>
                    </form>
                    <Table>
                        <TableHeader className="bg-zinc-900">
                            <TableRow className="border-zinc-800"><TableHead>Role</TableHead><TableHead>Scope</TableHead><TableHead className="text-right">Action</TableHead></TableRow>
                        </TableHeader>
                        <TableBody>
                            {userRoles.length === 0 ? (
                                <TableRow><TableCell colSpan={3} className="text-center text-zinc-500">No roles found.</TableCell></TableRow>
                            ) : (
                                userRoles.map((roleItem, idx) => (
                                    <TableRow key={idx} className="border-zinc-800">
                                        <TableCell><Badge variant="outline" className="text-indigo-400 border-indigo-900 bg-indigo-950/30">{roleItem.role}</Badge></TableCell>
                                        <TableCell className="font-mono text-xs text-zinc-400">{roleItem.store_id ? `Store: ${roleItem.store_id.slice(0,8)}` : roleItem.warehouse_id ? `WH: ${roleItem.warehouse_id.slice(0,8)}` : "Global"}</TableCell>
                                        <TableCell className="text-right"><Button size="icon" variant="ghost" className="text-red-500 hover:bg-red-950/50" onClick={() => handleRevoke(roleItem)}><Trash2 className="h-4 w-4" /></Button></TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>

      </div>
    </div>
  );
}