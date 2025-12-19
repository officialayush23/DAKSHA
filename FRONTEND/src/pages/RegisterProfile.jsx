// src/pages/RegisterProfilePage.jsx
import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import { Navigate, useNavigate } from "react-router-dom";

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

function RegisterSkeleton() {
  return (
    <AuthLayout>
      <Card className="border border-border/60 bg-background">
        <CardHeader>
          <Skeleton className="h-5 w-40 mb-1" />
          <Skeleton className="h-3 w-64" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-9 w-full rounded-md" />
            </div>
          ))}
          <Skeleton className="h-9 w-full rounded-md" />
        </CardContent>
        <CardFooter>
          <Skeleton className="h-3 w-56" />
        </CardFooter>
      </Card>
    </AuthLayout>
  );
}

export function RegisterProfilePage() {
  const { user, profile, refreshProfile, loading } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("+91");
  const [gender, setGender] = useState("");
  const [dob, setDob] = useState("");
  const [saving, setSaving] = useState(false);
  const [initializing, setInitializing] = useState(true);

  const hasPhone = profile && profile.phone_number;

  useEffect(() => {
    if (!loading) {
      setFullName(profile?.full_name || "");
      setPhone(profile?.phone_number || "+91");
      setGender(profile?.gender || "");
      setDob(profile?.date_of_birth || "");
      setInitializing(false);
    }
  }, [loading, profile]);

  if (!user && !loading) {
    return <Navigate to="/login" replace />;
  }

  const handleRegisterProfile = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);

      await api.post("/users/register", {
        full_name: fullName || null,
        phone_number: phone || null,
        gender: gender || null,
        date_of_birth: dob || null,
      });

      await refreshProfile();
      toast.success("Profile saved.");

      navigate("/home", { replace: true }); // ✅ REDIRECT HERE
    } catch (err) {
      console.error(err);
      toast.error("Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  if (profile?.phone_number && !loading) {
    return <Navigate to="/home" replace />;
  }

  if (loading || initializing) return <RegisterSkeleton />;

  return (
    <AuthLayout>
      <Card className="border border-border/60 bg-background">
        <CardHeader>
          <CardTitle className="text-xl font-semibold tracking-tight">
            Complete your profile
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground">
            Add phone and preferences for a better in-store & online experience.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form className="space-y-4" onSubmit={handleRegisterProfile}>
            <div className="space-y-1.5">
              <Label htmlFor="fullName">Full name</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                className="bg-background"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="phone">Phone (E.164)</Label>
              <Input
                id="phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91XXXXXXXXXX"
                className="bg-background"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="gender">Gender (optional)</Label>
              <Input
                id="gender"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                placeholder={profile?.gender || "men / women / unisex ..."}
                className="bg-background"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="dob">Date of birth (optional)</Label>
              <Input
                id="dob"
                type="date"
                value={dob || ""}
                onChange={(e) => setDob(e.target.value)}
                className="bg-background"
              />
            </div>

            {hasPhone && (
              <p className="text-[11px] text-emerald-500">
                Phone already on file: {profile.phone_number}
              </p>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={saving || loading}
            >
              {saving || loading ? "Saving..." : "Save profile"}
            </Button>
          </form>
        </CardContent>

        <CardFooter className="text-[11px] text-muted-foreground">
          You can edit these details later in your account settings.
        </CardFooter>
      </Card>
    </AuthLayout>
  );
}
