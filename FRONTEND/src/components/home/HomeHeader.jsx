import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { ModeToggle } from "@/components/use_ui/ModeToggle";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient";
import { trackSearch } from "@/lib/analytics";
import { useState } from "react";

export default function HomeHeader() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [q, setQ] = useState(searchParams.get("search") || "");
    const user = supabase.auth.getUser().data?.user;


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
                    className="font-semibold tracking-tight cursor-pointer"
                    onClick={() => navigate("/home")}
                >
                    Daksha
                </div>

                {/* Search */}
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input

                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        onKeyDown={handleSearch}
                        placeholder="Search products…"
                        className="pl-10 rounded-full"


                    />
                </div>

                {/* Right */}
                <div className="flex items-center gap-3">
                    <ModeToggle />
                    <Avatar
                        className="h-9 w-9 cursor-pointer"
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
