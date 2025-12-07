// src/pages/LoginPage.jsx
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

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

export function LoginPage() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) return <LoginSkeleton />;

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await login(email, password);
      toast.success("Signed in.");
      navigate("/register");
    } catch (err) {
      toast.error(err?.message || "Login failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <Card className="border border-border/60 bg-background">
        <CardHeader>
          <CardTitle className="text-xl font-semibold tracking-tight">
            Sign in
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Use your Supabase email & password.
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
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-background"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="loginPassword">Password</Label>
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
              className="w-full"
              disabled={submitting || loading}
            >
              {submitting || loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex flex-col gap-2 items-start">
          <p className="text-[11px] text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link
              to="/signup"
              className="underline underline-offset-4 hover:text-foreground"
            >
              Sign up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </AuthLayout>
  );
}
