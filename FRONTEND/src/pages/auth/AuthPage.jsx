import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/apiClient";

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { ModeToggle } from "../../components/use_ui/ModeToggle";

import { toast } from "sonner";

export function AuthPage() {
  const { login, signUp, profile, user, refreshProfile, loading } = useAuth();

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("+91");
  const [gender, setGender] = useState("");
  const [dob, setDob] = useState("");
  const [registerLoading, setRegisterLoading] = useState(false);

  const hasPhone = profile && profile.phone_number;

  /* -----------------------------------------
   * LOGIN
   * ----------------------------------------- */
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      setLoginLoading(true);
      await login(loginEmail, loginPassword);
      toast.success("Signed in successfully.");
    } catch (err) {
      toast.error(err?.message || "Login failed.");
    } finally {
      setLoginLoading(false);
    }
  };

  /* -----------------------------------------
   * SIGN UP
   * ----------------------------------------- */
  const handleSignUp = async (e) => {
    e.preventDefault();
    try {
      await signUp(signupEmail, signupPassword);
      toast.info("Check your email to verify your account.");
    } catch (err) {
      toast.error(err?.message || "Sign up failed.");
    }
  };

  /* -----------------------------------------
   * PROFILE COMPLETION
   * ----------------------------------------- */
  const handleRegisterProfile = async (e) => {
    e.preventDefault();
    try {
      setRegisterLoading(true);

      await api.post("/users/register", {
        full_name: fullName,
        phone_number: phone,
        gender: gender || null,
        date_of_birth: dob || null,
      });

      await refreshProfile();
      toast.success("Profile updated successfully.");
    } catch (err) {
      console.error(err);
      toast.error("Failed to update profile.");
    } finally {
      setRegisterLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="flex items-center justify-between px-6 py-4 border-b">
        <div className="font-semibold tracking-tight">Daksha Retail</div>
        <ModeToggle />
      </header>

      <main className="flex-1 flex items-center justify-center px-4">
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* -------------------------------------------------
           * LOGIN / SIGNUP CARD
           * ------------------------------------------------- */}
          <Card>
            <CardHeader>
              <CardTitle>Sign in</CardTitle>
              <CardDescription>
                Authenticate with Supabase email login.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* LOGIN FORM */}
              <form className="space-y-4" onSubmit={handleLogin}>
                <div className="space-y-2">
                  <Label htmlFor="loginEmail">Email</Label>
                  <Input
                    id="loginEmail"
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="loginPassword">Password</Label>
                  <Input
                    id="loginPassword"
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={loginLoading || loading}
                >
                  {loginLoading || loading ? "Signing in..." : "Sign in"}
                </Button>
              </form>

              <Separator />

              {/* SIGN UP FORM */}
              <form className="space-y-4" onSubmit={handleSignUp}>
                <div className="space-y-2">
                  <Label htmlFor="signupEmail">Create new account</Label>
                  <Input
                    id="signupEmail"
                    type="email"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signupPassword">Password</Label>
                  <Input
                    id="signupPassword"
                    type="password"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    required
                  />
                </div>

                <Button type="submit" variant="outline" className="w-full">
                  Sign up
                </Button>
              </form>
            </CardContent>

            <CardFooter>
              {user && (
                <p className="text-xs text-muted-foreground">
                  Logged in as {user.email}
                </p>
              )}
            </CardFooter>
          </Card>

          {/* -------------------------------------------------
           * PROFILE COMPLETION CARD
           * ------------------------------------------------- */}
          <Card>
            <CardHeader>
              <CardTitle>Complete your profile</CardTitle>
              <CardDescription>
                Add details for personalization and recommendations.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {!user ? (
                <p className="text-sm text-muted-foreground">
                  Sign in to complete your profile.
                </p>
              ) : (
                <form className="space-y-4" onSubmit={handleRegisterProfile}>
                  <div className="space-y-2">
                    <Label htmlFor="fullName">Full name</Label>
                    <Input
                      id="fullName"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder={profile?.full_name || ""}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone (E.164)</Label>
                    <Input
                      id="phone"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91XXXXXXXXXX"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="gender">Gender</Label>
                    <Input
                      id="gender"
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      placeholder={profile?.gender || "men / women / unisex"}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dob">Date of birth</Label>
                    <Input
                      id="dob"
                      type="date"
                      value={dob}
                      onChange={(e) => setDob(e.target.value)}
                    />
                  </div>

                  {hasPhone && (
                    <p className="text-xs text-green-500">
                      Phone on file: {profile.phone_number}
                    </p>
                  )}

                  <Button type="submit" className="w-full" disabled={registerLoading}>
                    {registerLoading ? "Saving..." : "Save profile"}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
