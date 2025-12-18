import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Store, ArrowRight, Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function KioskLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      toast.error("Login Failed", { description: "Please check your email and PIN/Password" });
      setLoading(false);
    } else {
      toast.success("Welcome Back!");
      // Redirect to Store Guide
      navigate("/kiosk/guide");
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=2070&auto=format&fit=crop')] bg-cover opacity-20" />
      
      <Card className="w-full max-w-md bg-zinc-950/90 border-zinc-800 backdrop-blur-xl p-8 relative z-10 shadow-2xl">
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-white rounded-full flex items-center justify-center mb-4 shadow-glow">
            <Store className="h-8 w-8 text-black" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Store Kiosk</h1>
          <p className="text-zinc-400 mt-2">Scan your member ID or login to access your personal shopping assistant.</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="space-y-2">
            <Input 
              type="email" 
              placeholder="Email Address" 
              className="h-14 text-lg bg-black/50 border-zinc-700 text-white focus:border-white transition-all"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Input 
              type="password" 
              placeholder="Password" 
              className="h-14 text-lg bg-black/50 border-zinc-700 text-white focus:border-white transition-all"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>

          <Button type="submit" disabled={loading} className="w-full h-14 text-lg font-bold bg-white text-black hover:bg-zinc-200 transition-transform active:scale-95">
            {loading ? <Loader2 className="animate-spin mr-2" /> : "Start Shopping"} 
            {!loading && <ArrowRight className="ml-2 h-5 w-5" />}
          </Button>
        </form>
        
        <div className="mt-6 text-center">
          <button className="text-zinc-500 text-sm hover:text-white underline">Continue as Guest</button>
        </div>
      </Card>
    </div>
  );
}