import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { 
  ShoppingBag, 
  Package, 
  LifeBuoy, 
  User, 
  LogOut, 
  Bot, 
  MapPin, 
  ShoppingCart,
  ChevronRight,
  Store
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";

// --- Header Component (Reusable) ---
// In a real app, move this to src/components/layout/Header.jsx
const DashboardHeader = ({ user, profile, logout, cartCount = 2 }) => {
  const navigate = useNavigate();
  
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-6 shadow-sm">
      <nav className="flex flex-1 items-center gap-6">
        <Link to="/dashboard" className="flex items-center gap-2 font-bold text-lg">
          <Store className="h-6 w-6 text-primary" />
          <span>Daksha Retail</span>
        </Link>
        <div className="hidden md:flex gap-6 text-sm font-medium text-muted-foreground">
          <Link to="/products" className="hover:text-foreground transition-colors">Shop</Link>
          <Link to="/orders" className="hover:text-foreground transition-colors">Orders</Link>
          <Link to="/support" className="hover:text-foreground transition-colors">Support</Link>
        </div>
      </nav>

      <div className="flex items-center gap-4">
        {/* Cart Button */}
        <Button variant="ghost" size="icon" className="relative" onClick={() => navigate("/cart")}>
          <ShoppingCart className="h-5 w-5" />
          {cartCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] text-primary-foreground">
              {cartCount}
            </span>
          )}
        </Button>

        {/* Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="secondary" size="icon" className="rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${profile?.full_name || "User"}`} />
                <AvatarFallback>U</AvatarFallback>
              </Avatar>
              <span className="sr-only">Toggle user menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/profile")}>
              <User className="mr-2 h-4 w-4" /> Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate("/orders")}>
              <Package className="mr-2 h-4 w-4" /> Orders
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate("/support")}>
              <LifeBuoy className="mr-2 h-4 w-4" /> Support
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="text-red-500 focus:text-red-500">
              <LogOut className="mr-2 h-4 w-4" /> Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default function Dashboard() {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-muted/10 flex flex-col">
      <DashboardHeader user={user} profile={profile} logout={logout} />

      <main className="flex-1 container mx-auto p-4 md:p-8 space-y-8">
        
        {/* 1. Hero / Welcome Section */}
        <section className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Welcome back, {profile?.full_name?.split(' ')[0] || "Shopper"}!</h1>
            <p className="text-muted-foreground mt-1">
              Your personalized AI shopping assistant is ready to help you.
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-white px-3 py-1 rounded-full border shadow-sm">
            <MapPin className="h-4 w-4 text-emerald-500" />
            <span>Nearest Store: <strong>Daksha Downtown (1.2km)</strong></span>
          </div>
        </section>

        {/* 2. Company Info / AI Value Prop */}
        <Card className="bg-gradient-to-r from-slate-900 to-slate-800 text-white border-none">
          <CardContent className="p-8 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-4 max-w-xl">
              <Badge variant="secondary" className="bg-emerald-500 text-white hover:bg-emerald-600 border-none">
                New AI Feature
              </Badge>
              <h2 className="text-2xl font-bold">Experience the Future of Retail</h2>
              <p className="text-slate-300">
                Seamlessly switch between online shopping and our in-store kiosks. 
                Ask our AI Agent to "Reserve this jacket at the Downtown store" and we'll handle the rest.
              </p>
              <Button onClick={() => navigate("/products")} variant="secondary" className="w-fit">
                Start Browsing
              </Button>
            </div>
            <div className="hidden md:flex h-32 w-32 items-center justify-center rounded-full bg-white/10 backdrop-blur-sm">
              <Bot className="h-16 w-16 text-emerald-400" />
            </div>
          </CardContent>
        </Card>

        {/* 3. Navigation Grid (Redirects) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          {/* Product / Shop */}
          <Card className="hover:shadow-lg transition-all cursor-pointer group" onClick={() => navigate("/products")}>
            <CardHeader>
              <ShoppingBag className="h-8 w-8 text-primary mb-2 group-hover:scale-110 transition-transform" />
              <CardTitle>Shop Catalog</CardTitle>
              <CardDescription>Browse our latest AI-curated collection.</CardDescription>
            </CardHeader>
            <CardFooter>
              <span className="text-sm font-medium text-primary flex items-center">Go to Shop <ChevronRight className="h-4 w-4 ml-1" /></span>
            </CardFooter>
          </Card>

          {/* Cart */}
          <Card className="hover:shadow-lg transition-all cursor-pointer group" onClick={() => navigate("/cart")}>
            <CardHeader>
              <ShoppingCart className="h-8 w-8 text-blue-500 mb-2 group-hover:scale-110 transition-transform" />
              <CardTitle>My Cart</CardTitle>
              <CardDescription>Review items and proceed to checkout.</CardDescription>
            </CardHeader>
            <CardFooter>
              <span className="text-sm font-medium text-blue-500 flex items-center">View Cart <ChevronRight className="h-4 w-4 ml-1" /></span>
            </CardFooter>
          </Card>

          {/* Orders */}
          <Card className="hover:shadow-lg transition-all cursor-pointer group" onClick={() => navigate("/orders")}>
            <CardHeader>
              <Package className="h-8 w-8 text-orange-500 mb-2 group-hover:scale-110 transition-transform" />
              <CardTitle>Orders & Returns</CardTitle>
              <CardDescription>Track shipments or buy again.</CardDescription>
            </CardHeader>
            <CardFooter>
              <span className="text-sm font-medium text-orange-500 flex items-center">Track History <ChevronRight className="h-4 w-4 ml-1" /></span>
            </CardFooter>
          </Card>

          {/* Profile */}
          <Card className="hover:shadow-lg transition-all cursor-pointer group" onClick={() => navigate("/profile")}>
            <CardHeader>
              <User className="h-8 w-8 text-purple-500 mb-2 group-hover:scale-110 transition-transform" />
              <CardTitle>Profile Settings</CardTitle>
              <CardDescription>Update preferences and payment methods.</CardDescription>
            </CardHeader>
            <CardFooter>
              <span className="text-sm font-medium text-purple-500 flex items-center">Edit Profile <ChevronRight className="h-4 w-4 ml-1" /></span>
            </CardFooter>
          </Card>
        </div>

        {/* 4. Support & Kiosk Area */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
           <Card className="border-l-4 border-l-red-500">
             <CardHeader>
               <CardTitle className="flex items-center gap-2">
                 <LifeBuoy className="h-5 w-5" /> Need Help?
               </CardTitle>
               <CardDescription>
                 Our AI support agent can resolve 80% of issues instantly.
               </CardDescription>
             </CardHeader>
             <CardContent>
               <Button variant="outline" className="w-full" onClick={() => navigate("/support")}>
                 Open Support Ticket
               </Button>
             </CardContent>
           </Card>

           <Card className="bg-muted/50 border-dashed">
             <CardHeader>
               <CardTitle className="flex items-center gap-2">
                 <Store className="h-5 w-5" /> In-Store Kiosk Mode
               </CardTitle>
               <CardDescription>
                 Switch to Kiosk view for physical store terminals.
               </CardDescription>
             </CardHeader>
             <CardContent>
               <Button variant="ghost" className="w-full" onClick={() => toast.info("Switching to Kiosk Mode...")}>
                 Launch Kiosk Login
               </Button>
             </CardContent>
           </Card>
        </div>

      </main>

      {/* Floating Chatbot Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <Button 
          className="h-14 w-14 rounded-full shadow-xl bg-primary hover:bg-primary/90 transition-transform hover:scale-105"
          onClick={() => navigate("/chat")} // Or open a chat modal
        >
          <Bot className="h-8 w-8 text-white" />
          <span className="sr-only">Open AI Chat</span>
        </Button>
      </div>

    </div>
  );
}