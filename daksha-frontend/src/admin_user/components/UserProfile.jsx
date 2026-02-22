import React, { useState, useEffect } from 'react';
import { UserAdminService } from "../lib/userApi";
import UserActions from './UserActions';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, TrendingUp, Award, Calendar, Activity, Ticket, Inbox } from 'lucide-react';

export default function UserProfile({ userId }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadFullProfile = async () => {
    setLoading(true);
    try {
      const results = await Promise.allSettled([
        UserAdminService.getUserProfile(userId),
        UserAdminService.getUserSpend(userId),
        UserAdminService.getUserLoyalty(userId),
        UserAdminService.getUserOrders(userId),
        UserAdminService.getUserComplaints(userId),
        UserAdminService.getUserPickups(userId),
        UserAdminService.getUserEvents(userId),
        UserAdminService.getUserPersonalizedCoupons(userId)
      ]);

      // Helper to extract data safely. Returns fallback if request failed.
      const getData = (index, fallback = []) => 
        results[index].status === 'fulfilled' ? results[index].value : fallback;

      setDetails({
        profile: getData(0, {}),
        spend: getData(1, { total_spent: 0, order_count: 0 }),
        loyalty: getData(2, []),
        orders: getData(3, []),
        complaints: getData(4, []),
        pickups: getData(5, []),
        events: getData(6, []),
        coupons: getData(7, [])
      });
    } catch (error) {
      console.error("Critical error mapping profile data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (userId) loadFullProfile(); }, [userId]);

  if (loading) return (
    <div className="p-24 flex flex-col items-center justify-center gap-4 text-muted-foreground">
      <Loader2 className="animate-spin h-8 w-8" />
      <p className="text-sm font-medium">Fetching User Intelligence...</p>
    </div>
  );

  // Helper for empty states within tabs
  const EmptyState = ({ message }) => (
    <div className="flex flex-col items-center justify-center py-10 text-muted-foreground opacity-60">
      <Inbox className="h-8 w-8 mb-2 stroke-1" />
      <p className="text-[11px]">{message}</p>
    </div>
  );

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500 pb-10">
      {/* Financial & Loyalty Summary */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="border-l-4 border-l-green-500 shadow-sm overflow-hidden">
          <CardHeader className="pb-1 pt-4 px-4 text-[10px] font-bold uppercase text-muted-foreground flex flex-row justify-between">
            Revenue <TrendingUp className="h-3 w-3" />
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold">₹{details.spend.total_spent || 0}</div>
            <p className="text-[10px] text-muted-foreground">{details.spend.order_count || 0} orders</p>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-blue-500 shadow-sm overflow-hidden">
          <CardHeader className="pb-1 pt-4 px-4 text-[10px] font-bold uppercase text-muted-foreground flex flex-row justify-between">
            Loyalty <Award className="h-3 w-3" />
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-2xl font-bold text-blue-600">
              {details.loyalty.reduce((acc, curr) => acc + (curr.points || 0), 0)} pts
            </div>
            <p className="text-[10px] text-muted-foreground">Current Balance</p>
          </CardContent>
        </Card>
      </div>

      <UserActions userId={userId} onUpdate={loadFullProfile} />

      <Tabs defaultValue="orders" className="w-full">
        <TabsList className="grid w-full grid-cols-5 h-9 bg-muted/50 p-1">
          <TabsTrigger value="orders" className="text-[10px] data-[state=active]:shadow-sm">Orders</TabsTrigger>
          <TabsTrigger value="loyalty" className="text-[10px] data-[state=active]:shadow-sm">Points</TabsTrigger>
          <TabsTrigger value="pickups" className="text-[10px] data-[state=active]:shadow-sm">Pickups</TabsTrigger>
          <TabsTrigger value="coupons" className="text-[10px] data-[state=active]:shadow-sm">Offers</TabsTrigger>
          <TabsTrigger value="events" className="text-[10px] data-[state=active]:shadow-sm">Activity</TabsTrigger>
        </TabsList>

        {/* Orders Tab */}
        <TabsContent value="orders" className="pt-2">
          {details.orders.length > 0 ? (
            <div className="rounded-md border text-xs bg-background overflow-hidden">
              <Table>
                <TableHeader className="bg-muted/30">
                  <TableRow>
                    <TableHead className="h-8">ID</TableHead>
                    <TableHead className="h-8">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {details.orders.map(o => (
                    <TableRow key={o.id} className="hover:bg-muted/20">
                      <TableCell className="font-mono text-[10px] py-2">{o.id.slice(0, 8)}</TableCell>
                      <TableCell className="py-2">
                        <Badge variant="secondary" className="text-[9px] px-1.5 py-0 uppercase font-bold tracking-tight">
                          {o.order_status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : <EmptyState message="No orders found for this user" />}
        </TabsContent>

        {/* Loyalty Tab */}
        <TabsContent value="loyalty" className="pt-2 space-y-2">
          {details.loyalty.length > 0 ? details.loyalty.map(log => (
            <div key={log.id} className="flex justify-between items-center p-2 border rounded-md text-[10px] bg-background hover:border-blue-200 transition-colors">
              <div>
                <div className="font-bold uppercase text-[9px] text-muted-foreground">{log.transaction_type}</div>
                <div className="text-foreground/80">{log.reference_note || "Standard allocation"}</div>
              </div>
              <div className={log.points > 0 ? "text-green-600 font-bold" : "text-red-600 font-bold"}>
                {log.points > 0 ? "+" : ""}{log.points}
              </div>
            </div>
          )) : <EmptyState message="No loyalty transactions recorded" />}
        </TabsContent>

        {/* Pickups Tab */}
        <TabsContent value="pickups" className="pt-2 space-y-2">
          {details.pickups.length > 0 ? details.pickups.map(p => (
            <div key={p.id} className="p-3 border rounded-md text-[10px] bg-background flex flex-col gap-2 hover:border-primary/30 transition-colors">
              <div className="flex justify-between items-center font-bold uppercase text-[9px]">
                <span className="text-muted-foreground">Pickup Ref: {p.id.slice(0, 8)}</span>
                <Badge variant="outline" className="text-[8px] h-4 border-primary/20 bg-primary/5 text-primary">
                  {p.status}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-foreground/70 bg-muted/30 p-1.5 rounded">
                <Calendar className="w-3 h-3 text-primary/60" /> 
                <span>Scheduled: {p.scheduled_time ? new Date(p.scheduled_time).toLocaleString() : "TBD"}</span>
              </div>
            </div>
          )) : <EmptyState message="No store pickups scheduled" />}
        </TabsContent>

        {/* Personalized Coupons */}
        <TabsContent value="coupons" className="pt-2 space-y-2">
          {details.coupons.length > 0 ? details.coupons.map(c => (
            <div key={c.id} className="flex justify-between items-center p-3 border rounded-md text-[10px] bg-background border-l-4 border-l-orange-500 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-50 rounded-full">
                  <Ticket className="w-4 h-4 text-orange-600" />
                </div>
                <div>
                  <div className="font-bold text-[11px]">{c.offer_name || "Personalized Discount"}</div>
                  <div className="text-muted-foreground">Value: <span className="text-foreground font-semibold">₹{c.discount_value}</span></div>
                </div>
              </div>
              <Badge variant={c.is_redeemed ? "outline" : "default"} className={c.is_redeemed ? "opacity-50" : "bg-orange-600"}>
                {c.is_redeemed ? "Redeemed" : "Active"}
              </Badge>
            </div>
          )) : <EmptyState message="No personalized offers issued" />}
        </TabsContent>

        {/* Activity/Events Log */}
        <TabsContent value="events" className="pt-2">
          {details.events.length > 0 ? (
            <div className="space-y-1.5 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
              {details.events.map(e => (
                <div key={e.id} className="flex gap-3 p-2.5 border rounded-lg bg-muted/10 text-[10px] hover:bg-muted/20 transition-all border-transparent hover:border-muted-foreground/10">
                  <div className="mt-0.5 p-1 bg-background rounded border shadow-sm">
                    <Activity className="w-3 h-3 text-muted-foreground" />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <span className="font-bold text-foreground/90 uppercase tracking-tight">{e.event_type.replace(/_/g, ' ')}</span>
                      <span className="text-[8px] text-muted-foreground tabular-nums">
                        {new Date(e.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-muted-foreground text-[9px] mt-0.5 font-medium">
                      {new Date(e.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : <EmptyState message="No recent system activity found" />}
        </TabsContent>
      </Tabs>
    </div>
  );
}