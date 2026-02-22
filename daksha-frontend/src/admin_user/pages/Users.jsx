import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { UserAdminService } from '../lib/userApi';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Search, ChevronRight } from 'lucide-react';

export default function UserList() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const { userId } = useParams(); // Get the selected ID from the URL

  useEffect(() => {
    UserAdminService.listUsers().then(setUsers);
  }, []);

  const filtered = users.filter(u => 
    u.email?.toLowerCase().includes(search.toLowerCase()) || 
    u.username?.toLowerCase().includes(search.toLowerCase()) ||
    u.name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input 
          placeholder="Search users by name, email, or username..." 
          className="pl-9" 
          value={search} 
          onChange={e => setSearch(e.target.value)} 
        />
      </div>
      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead>User Details</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length > 0 ? (
              filtered.map(user => (
                <TableRow 
                  key={user.id} 
                  className={`cursor-pointer transition-colors ${userId === user.id ? 'bg-muted border-l-4 border-l-primary' : ''}`}
                  onClick={() => navigate(`/admin/users/${user.id}`)} // Navigate via URL
                >
                  <TableCell>
                    <div className="font-medium">{user.name || user.username || "Unnamed User"}</div>
                    <div className="text-xs text-muted-foreground">{user.email}</div>
                  </TableCell>
                  <TableCell className="text-right">
                    <ChevronRight className={`ml-auto h-4 w-4 transition-transform ${userId === user.id ? 'rotate-90' : ''}`} />
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={2} className="h-24 text-center text-muted-foreground">
                  No users found matching "{search}"
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}