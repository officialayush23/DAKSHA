// src/pages/SignupPage.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
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

function SignupSkeleton() {
  return (
    <AuthLayout>
      <Card className="border border-border/60 bg-background">
        <CardHeader>
          <Skeleton className="h-5 w-32 mb-1" />
          <Skeleton className="h-3 w-48" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <Skeleton className="h-4 w-12" />
            <Skeleton className="h-9 w-full rounded-md" />
          </div>
          <div className="space-y-3">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-9 w-full rounded-md" />
          </div>
          <Skeleton className="h-9 w-full rounded-md" />
        </CardContent>
        <CardFooter>
          <Skeleton className="h-3 w-52" />
        </CardFooter>
      </Card>
    </AuthLayout>
  );
}

export function SignupPage() {
  const { signUp, loading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) return <SignupSkeleton />;

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await signUp(email, password);
      toast.info("Check your email to verify your account.");
      navigate("/login");
    } catch (err) {
      toast.error(err?.message || "Sign up failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      <Card className="border border-border/60 bg-background">
        <CardHeader>
          <CardTitle className="text-xl font-semibold tracking-tight">
            Create account
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            We use Supabase email auth.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="space-y-4" onSubmit={handleSignup}>
            <div className="space-y-1.5">
              <Label htmlFor="signupEmail">Email</Label>
              <Input
                id="signupEmail"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="bg-background"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="signupPassword">Password</Label>
              <Input
                id="signupPassword"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-background"
                required
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              variant="outline"
              disabled={submitting || loading}
            >
              {submitting || loading ? "Creating..." : "Sign up"}
            </Button>
          </form>
        </CardContent>

        <CardFooter>
          <p className="text-[11px] text-muted-foreground">
            Already have an account?{" "}
            <Link
              to="/login"
              className="underline underline-offset-4 hover:text-foreground"
            >
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </AuthLayout>
  );
}
