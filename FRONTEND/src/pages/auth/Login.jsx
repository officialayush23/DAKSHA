import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import apiClient from "@/lib/apiClient";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const { setToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ phone_number: "" });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const guest_id = localStorage.getItem("guest_id") || crypto.randomUUID();
      localStorage.setItem("guest_id", guest_id);
      
      const response = await apiClient.post("/auth/login-phone", { ...formData, guest_id });

      if (response.user_id) {
        setToken(response.user_id);

        // Sync user profile
        const syncResponse = await apiClient.post("/auth/sync");

        if (syncResponse.user.full_name) {
          navigate("/");
        } else {
          navigate("/complete-profile");
        }
      } else {
        throw new Error(response.detail || "Login failed");
      }
    } catch (error) {
      alert("Login failed: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Welcome</CardTitle>
        <CardDescription>Sign in or create an account</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Phone Number</Label>
            <Input
              type="tel"
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Continue with Phone Number"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}