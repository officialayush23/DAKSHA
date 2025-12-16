import React, { useState } from "react";
import { 
  ShoppingCart, 
  Truck, 
  CheckCircle2, 
  Clock, 
  MoreHorizontal,
  MapPin,
  Box
} from "lucide-react";
import { Link } from "react-router-dom";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

// Mock Data (Replace with API call to /orders/history)
const mockOrders = [
  {
    id: "ORD-7829",
    customer: { name: "Aarav Patel", email: "aarav@example.com" },
    type: "Pickup", // Pickup or Ship
    status: "Pending", // Pending, Packed, Shipped
    items: 3,
    total: 1299.00,
    time: "10 mins ago",
  },
  {
    id: "ORD-7830",
    customer: { name: "Priya Sharma", email: "priya@example.com" },
    type: "Ship",
    status: "Processing",
    items: 1,
    total: 450.00,
    time: "25 mins ago",
  },
  {
    id: "ORD-7831",
    customer: { name: "Rohan Gupta", email: "rohan@example.com" },
    type: "Pickup",
    status: "Ready",
    items: 5,
    total: 2499.00,
    time: "1 hour ago",
  },
];

export default function OrderFulfillment() {
  const [filter, setFilter] = useState("all");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Order Fulfillment</h2>
          <p className="text-muted-foreground">
            Manage incoming orders for pickup and local delivery.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Clock className="mr-2 h-4 w-4" /> History
          </Button>
          <Button>
            <CheckCircle2 className="mr-2 h-4 w-4" /> Sync Orders
          </Button>
        </div>
      </div>

      <Tabs defaultValue="active" className="w-full">
        <TabsList>
          <TabsTrigger value="active">Active Orders</TabsTrigger>
          <TabsTrigger value="pickup">Pickup</TabsTrigger>
          <TabsTrigger value="shipping">Shipping</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>
        
        <TabsContent value="active" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Queue</CardTitle>
              <CardDescription>
                Orders waiting to be packed or picked up.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order ID</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Items</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockOrders.map((order) => (
                    <TableRow key={order.id}>
                      <TableCell className="font-medium">
                        {order.id}
                        <div className="text-xs text-muted-foreground">{order.time}</div>
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback>{order.customer.name.charAt(0)}</AvatarFallback>
                          </Avatar>
                          <div className="flex flex-col">
                            <span className="font-medium text-sm">{order.customer.name}</span>
                            <span className="text-xs text-muted-foreground">{order.customer.email}</span>
                          </div>
                        </div>
                      </TableCell>

                      <TableCell>
                        <Badge variant="outline" className="flex w-fit items-center gap-1">
                          {order.type === "Pickup" ? <MapPin className="h-3 w-3" /> : <Truck className="h-3 w-3" />}
                          {order.type}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        <StatusBadge status={order.status} />
                      </TableCell>

                      <TableCell>
                        <div className="flex items-center gap-1 text-sm">
                          <Box className="h-3 w-3 text-muted-foreground" />
                          {order.items} items
                        </div>
                      </TableCell>

                      <TableCell className="text-right">₹{order.total}</TableCell>

                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <span className="sr-only">Open menu</span>
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuItem>View Details</DropdownMenuItem>
                            <DropdownMenuItem>Print Packing Slip</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-green-600">Mark as Packed</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        {/* Other tabs can reuse the table with filtered data */}
      </Tabs>
    </div>
  );
}

// Helper Component for Status Colors
function StatusBadge({ status }) {
  const styles = {
    Pending: "bg-yellow-100 text-yellow-800 hover:bg-yellow-100",
    Processing: "bg-blue-100 text-blue-800 hover:bg-blue-100",
    Ready: "bg-green-100 text-green-800 hover:bg-green-100",
    Shipped: "bg-gray-100 text-gray-800 hover:bg-gray-100",
  };

  return (
    <Badge className={`${styles[status] || "bg-secondary"} border-0`}>
      {status}
    </Badge>
  );
}