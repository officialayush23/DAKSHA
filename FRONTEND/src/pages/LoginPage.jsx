import React, { useState, useEffect } from "react";
import { useNavigate, Link, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { supabase } from "@/lib/supabaseClient"; // Import Supabase directly

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";

import { AuthLayout } from "@/components/layout/AuthLayout";

// --- SKELETON COMPONENT ---
function LoginSkeleton() {
  return (
    <AuthLayout>
      <Card className="border border-border/60 bg-background">
        <CardHeader>
          <Skeleton className="h-5 w-28 mb-1" />
          <Skeleton className="h-3 w-40" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Skeleton className="h-4 w-14" />
            <Skeleton className="h-9 w-full rounded-md" />
          </div>
          <div className="space-y-3">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-9 w-full rounded-md" />
          </div>
          <Skeleton className="h-9 w-full rounded-md" />
        </CardContent>
        <CardFooter>
          <Skeleton className="h-3 w-40" />
        </CardFooter>
      </Card>
    </AuthLayout>
  );
}

// --- MAIN PAGE COMPONENT ---
export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false); // Local loading state
  const [pageLoading, setPageLoading] = useState(true); // Page load check

  // Check if already logged in
  useEffect(() => {
    const checkSession = async () => {
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        navigate("/", { replace: true });
      }
      setPageLoading(false);
    };
    checkSession();
  }, [navigate]);

  if (pageLoading) return <LoginSkeleton />;

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 1. Direct Supabase Call (Fixes "login is not a function")
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password: password,
      });

      if (error) throw error;

      // 2. Success Logic
      toast.success("Signed in successfully");
      
      // 3. Determine specific redirect based on role (Optional)
      // For now, go to where they came from or home
      const returnTo = location.state?.from?.pathname || "/";
      navigate(returnTo, { replace: true });

    } catch (err) {
      console.error("Login Error:", err);
      toast.error(err.message || "Invalid credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <Card className="border border-border/60 bg-background shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-semibold tracking-tight">
            Sign in
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Enter your credentials to access your account.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="space-y-4" onSubmit={handleLogin}>
            <div className="space-y-1.5">
              <Label htmlFor="loginEmail">Email</Label>
              <Input
                id="loginEmail"
                type="email"
                autoComplete="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-background"
                required
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="loginPassword">Password</Label>
                <Link 
                  to="/forgot-password" 
                  className="text-[10px] text-muted-foreground hover:text-primary transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <Input
                id="loginPassword"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-background"
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full font-medium"
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex flex-col gap-2 items-start border-t border-border/40 pt-4 bg-muted/20">
          <p className="text-[11px] text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link
              to="/signup"
              className="underline underline-offset-4 hover:text-foreground font-medium text-foreground/80"
            >
              Sign up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </AuthLayout>
  );
}