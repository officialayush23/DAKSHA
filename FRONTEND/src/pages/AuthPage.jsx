import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/apiClient";
import { useNavigate } from "react-router-dom";

import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { ModeToggle } from "@/components/use_ui/ModeToggle";
import { toast } from "sonner";

export function AuthPage() {
  const navigate = useNavigate();
  const { login, signUp, user, profile, refreshProfile, loading } = useAuth();

  useEffect(() => {
    if (profile?.full_name && profile?.phone_number) {
      navigate("/products");
    }
  }, [profile]);

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

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      setLoginLoading(true);
      const loggedInUser = await login(loginEmail, loginPassword);

      // 🔥 LOG TOKEN  
      console.log("🔑 Token received after login:", loggedInUser?.access_token);
      console.log("🔐 Axios Authorization header now:",
        api.defaults.headers.common["Authorization"]
      );

      toast.success("Signed in successfully.");
    } catch (err) {
      toast.error(err?.message || "Login failed.");
    } finally {
      setLoginLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    try {
      await signUp(signupEmail, signupPassword);
      toast.info("Check your email to verify your account.");
    } catch (err) {
      toast.error(err?.message || "Sign up failed.");
    }
  };

  const handleRegisterProfile = async (e) => {
    e.preventDefault();
    try {
      setRegisterLoading(true);

      // 🔥 LOG TOKEN BEFORE REQUEST
      console.log("📤 Token before /users/register:", api.defaults.headers.common["Authorization"]);

      await api.post("/users/register", {
        full_name: fullName || null,
        phone_number: phone || null,
        gender: gender || null,
        date_of_birth: dob || null,
      });

      await refreshProfile();
      toast.success("Profile saved!");

      navigate("/products");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to update profile.");
    } finally {
      setRegisterLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="border-b px-6 py-4 flex justify-between items-center">
        <h1 className="font-semibold tracking-tight">Daksha Retail</h1>
        <ModeToggle />
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Welcome</CardTitle>
              <CardDescription>Sign in or create a new account</CardDescription>
            </CardHeader>

            <CardContent className="space-y-8">
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                  />
                </div>

                <Button className="w-full" disabled={loginLoading || loading}>
                  {loginLoading ? "Signing in..." : "Sign in"}
                </Button>
              </form>

              <Separator />

              <form onSubmit={handleSignUp} className="space-y-4">
                <div className="space-y-2">
                  <Label>Create account</Label>
                  <Input
                    type="email"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input
                    type="password"
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                  />
                </div>

                <Button variant="outline" className="w-full">
                  Sign up
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Complete Profile</CardTitle>
              <CardDescription>Required to continue to the store</CardDescription>
            </CardHeader>

            <CardContent>
              {!user ? (
                <Skeleton className="h-32 w-full" />
              ) : (
                <form onSubmit={handleRegisterProfile} className="space-y-4">
                  <div>
                    <Label>Full name</Label>
                    <Input
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder={profile?.full_name || "Your Name"}
                    />
                  </div>

                  <div>
                    <Label>Phone Number (E.164)</Label>
                    <Input
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91XXXXXXXXXX"
                    />
                  </div>

                  <div>
                    <Label>Gender</Label>
                    <Input
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      placeholder="men / women / unisex"
                    />
                  </div>

                  <div>
                    <Label>Date of Birth</Label>
                    <Input
                      type="date"
                      value={dob}
                      onChange={(e) => setDob(e.target.value)}
                    />
                  </div>

                  <Button className="w-full" disabled={registerLoading}>
                    {registerLoading ? "Saving..." : "Save & Continue"}
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

export default AuthPage;
