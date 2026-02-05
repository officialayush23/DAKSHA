import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { OrderService } from '../lib/api';
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Package } from 'lucide-react';
import { format } from 'date-fns';

export default function OrdersPage() {
  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => OrderService.getAll().then(res => res),
  });

  if (isLoading) return <div className="h-96 flex items-center justify-center"><Loader2 className="animate-spin"/></div>;

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-serif font-bold mb-8">Your Orders</h1>
      
      {!orders || orders.length === 0 ? (
        <div className="text-center py-20 bg-zinc-50 rounded-3xl">
          <Package className="w-12 h-12 mx-auto mb-4 text-zinc-300" />
          <p className="text-zinc-500">No orders yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map(order => (
            <Card key={order.order_id} className="p-6 flex flex-col md:flex-row justify-between gap-6 hover:shadow-md transition-shadow">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-mono text-xs text-zinc-400">#{order.order_id.slice(0,8)}</span>
                  <Badge variant="outline" className="uppercase text-[10px] tracking-wider">{order.status}</Badge>
                </div>
                <div className="text-sm text-zinc-500">
                  Ordered on {format(new Date(order.created_at), 'PPP')}
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-sm text-zinc-400">Total</div>
                  <div className="font-bold text-lg">₹{order.total}</div>
                </div>
                <Button variant="secondary" className="rounded-full">View Details</Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}