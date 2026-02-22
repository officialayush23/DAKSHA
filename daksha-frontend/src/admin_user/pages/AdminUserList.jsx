import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronRight, Mail, Calendar, Shield, User as UserIcon } from 'lucide-react';

// FIX: Import the AdminUserService object instead of apiRequest
import { AdminUserService } from '@/lib/adminUserService'; 

import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { toast } from 'sonner';

export default function AdminUserList() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  const fetchUsers = async () => {
    try {
      setLoading(true);
      
      // FIX: Use the dedicated method from your service
      const response = await AdminUserService.listUsers(100, 0);
      
      // Ensure we extract the array regardless of backend wrapping
      const data = response?.data || response || [];
      const userList = Array.isArray(data) ? data : (data.items || []);
      
      setUsers(userList);
    } catch (error) {
      console.error("Failed to fetch users", error);
      toast.error("Could not load the user directory.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Filter users locally based on search term
  const filteredUsers = users.filter(user => 
    (user.name?.toLowerCase() || "").includes(searchTerm.toLowerCase()) ||
    (user.email?.toLowerCase() || "").includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* --- HEADER & SEARCH --- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 bg-white p-8 rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
        <div>
          <h2 className="text-3xl font-serif font-bold tracking-tight text-zinc-900 mb-2">All Users</h2>
          <p className="text-sm font-medium text-zinc-400">Manage and view customer profiles, orders, and sessions.</p>
        </div>

        <div className="relative w-full md:w-[350px]">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-4 h-4" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name or email..."
            className="pl-12 py-6 rounded-2xl bg-zinc-50 border-transparent focus-visible:ring-2 focus-visible:ring-black/5 focus-visible:border-zinc-300 transition-all text-sm font-medium shadow-inner"
          />
        </div>
      </div>

      {/* --- USERS LIST --- */}
      <div className="bg-white rounded-[2.5rem] border border-zinc-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] overflow-hidden">
        
        {/* Table Header (Hidden on small screens) */}
        <div className="hidden md:grid grid-cols-12 gap-4 p-6 border-b border-zinc-50 bg-zinc-50/50 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">
          <div className="col-span-5 pl-4">Customer</div>
          <div className="col-span-3">Role</div>
          <div className="col-span-3">Joined Date</div>
          <div className="col-span-1 text-right pr-4">Action</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-zinc-50">
          {loading ? (
            // Loading Skeletons
            Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center p-6 gap-6">
                <Skeleton className="w-12 h-12 rounded-full" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-5 w-48 rounded-md" />
                  <Skeleton className="h-4 w-32 rounded-md" />
                </div>
              </div>
            ))
          ) : filteredUsers.length === 0 ? (
            // Empty State
            <div className="p-16 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-zinc-50 rounded-full flex items-center justify-center mb-4 border border-zinc-100">
                <Search className="text-zinc-300" size={24} />
              </div>
              <h3 className="text-lg font-bold text-zinc-900 mb-1">No users found</h3>
              <p className="text-sm text-zinc-400 font-medium">Try adjusting your search term.</p>
            </div>
          ) : (
            // User Rows
            <AnimatePresence>
              {filteredUsers.map((user, index) => {
                const joinedDate = new Date(user.created_at).toLocaleDateString('en-US', {
                  month: 'short', day: 'numeric', year: 'numeric'
                });
                const initials = (user.name || user.email || "U").charAt(0).toUpperCase();
                const isAdmin = user.role === 'admin';

                return (
                  <motion.div
                    key={user.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.02, duration: 0.3 }}
                  >
                    <Link 
                      to={`/admin/users/${user.id}`} 
                      className="group grid grid-cols-1 md:grid-cols-12 gap-4 p-6 items-center hover:bg-[#F8F9FA] transition-colors duration-300"
                    >
                      
                      {/* Customer Info */}
                      <div className="col-span-1 md:col-span-5 flex items-center gap-4">
                        <Avatar className="h-12 w-12 border border-zinc-200 shadow-sm group-hover:scale-105 transition-transform duration-500">
                          <AvatarFallback className={`${isAdmin ? 'bg-zinc-900 text-white' : 'bg-zinc-100 text-zinc-600'} font-serif font-bold text-lg`}>
                            {initials}
                          </AvatarFallback>
                        </Avatar>
                        <div className="overflow-hidden">
                          <h4 className="font-bold text-zinc-900 text-base truncate group-hover:text-black transition-colors">
                            {user.name || "Unknown User"}
                          </h4>
                          <p className="text-xs font-medium text-zinc-400 truncate flex items-center gap-1.5 mt-0.5">
                            <Mail size={12} /> {user.email}
                          </p>
                        </div>
                      </div>

                      {/* Role Badge */}
                      <div className="col-span-1 md:col-span-3 flex items-center mt-2 md:mt-0">
                        <Badge className={`px-3 py-1 text-[10px] font-bold uppercase tracking-widest shadow-none border ${
                          isAdmin 
                            ? 'bg-zinc-900 text-white hover:bg-zinc-800' 
                            : 'bg-white text-zinc-500 border-zinc-200 hover:bg-zinc-50'
                        }`}>
                          {isAdmin ? <Shield size={10} className="mr-1.5" /> : <UserIcon size={10} className="mr-1.5" />}
                          {user.role || 'customer'}
                        </Badge>
                      </div>

                      {/* Joined Date */}
                      <div className="col-span-1 md:col-span-3 flex items-center mt-2 md:mt-0 text-xs font-medium text-zinc-500 gap-2">
                        <Calendar size={14} className="text-zinc-300" />
                        {joinedDate}
                      </div>

                      {/* Action Icon */}
                      <div className="col-span-1 md:col-span-1 flex items-center justify-end mt-4 md:mt-0">
                        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white border border-zinc-200 text-zinc-400 group-hover:bg-zinc-900 group-hover:text-white group-hover:border-zinc-900 transition-all duration-300 shadow-sm">
                          <ChevronRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                        </div>
                      </div>

                    </Link>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          )}
        </div>
      </div>
    </div>
  );
}