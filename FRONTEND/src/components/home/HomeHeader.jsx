// src/components/home/HomeHeader.jsx
import React, { useState, useEffect } from "react";
import { Search, Bell } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ModeToggle } from "@/components/use_ui/ModeToggle";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient";
import { trackSearch } from "@/lib/analytics";
import { useNotificationSocket } from "@/hooks/useNotificationSocket";

export default function HomeHeader() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    
    // 1. Sync local state with URL param
    const [q, setQ] = useState(searchParams.get("search") || "");
    const [unreadCount, setUnreadCount] = useState(0);
    const user = supabase.auth.getUser().data?.user;

    useEffect(() => {
        setQ(searchParams.get("search") || "");
    }, [searchParams]);

    // 2. Real-time Notifications Hook
    useNotificationSocket(() => {
        setUnreadCount(prev => prev + 1);
    });

    // 3. Handle Search Enter Key
    const handleSearch = (e) => {
        if (e.key === "Enter" && q.trim()) {
            trackSearch(q);
            // Redirect to Products Page with query param
            navigate(`/products?search=${encodeURIComponent(q)}`);
        }
    };

    return (
        <div className="sticky top-0 z-40 border-b backdrop-blur bg-background/80">
            <div className="h-16 px-4 md:px-8 flex items-center gap-4">

                {/* Brand */}
                <div
                    className="font-semibold tracking-tight cursor-pointer text-xl"
                    onClick={() => navigate("/home")}
                >
                    Daksha
                </div>

                {/* Search Bar (Desktop) */}
                <div className="flex-1 relative max-w-md ml-4 hidden md:block">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        onKeyDown={handleSearch}
                        placeholder="Search products..."
                        className="pl-10 rounded-full bg-muted/50 border-muted-foreground/20 focus:bg-background transition-all"
                    />
                </div>

                {/* Mobile Search Icon */}
                <Button variant="ghost" size="icon" className="md:hidden ml-auto" onClick={() => navigate("/products")}>
                    <Search className="h-5 w-5" />
                </Button>

                {/* Right Actions */}
                <div className="flex items-center gap-2">
                    {/* Notification Bell */}
                    <Button variant="ghost" size="icon" className="relative" onClick={() => navigate("/profile?tab=notifications")}>
                        <Bell className="h-5 w-5" />
                        {unreadCount > 0 && (
                            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                        )}
                    </Button>

                    <ModeToggle />
                    
                    <Avatar
                        className="h-9 w-9 cursor-pointer border border-border"
                        onClick={() => navigate("/profile")}
                    >
                        <AvatarImage src={user?.user_metadata?.avatar_url} />
                        <AvatarFallback>
                            {user?.email?.[0]?.toUpperCase() || "U"}
                        </AvatarFallback>
                    </Avatar>
                </div>
            </div>
        </div>
    );
}