import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { toast } from 'sonner'; // Notification Library

// Shadcn UI Components (Ensure these are installed)
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export default function AuthPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(''); // Mock OTP for backend demo
  
  // Ensure we have a Guest ID (Cookie) on mount
  useEffect(() => {
    if (!localStorage.getItem('daksha_guest_id')) {
      localStorage.setItem('daksha_guest_id', crypto.randomUUID());
    }
  }, []);

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 1. Get the Guest ID we've been using
      const guestId = localStorage.getItem('daksha_guest_id');

      // 2. Call the "Upsert" API (Login/Register + Merge)
      // In a real app, verify OTP first. Here we simulate it.
      const response = await api.post('/auth/login', {
        phone_number: phone, // Must be E.164 (e.g. +91...)
        guest_id: guestId
      });

      // 3. Success! Save Token
      // IMPORTANT: Your backend /auth/login currently returns { user_id, message }.
      // You need a REAL JWT here.
      // Option A: If using Supabase Auth on Frontend, get session.access_token there.
      // Option B: If backend generates it, ensure backend sends { access_token: "..." }
      
      // Assuming backend sends token or we simulate one for now:
      const token = response.data.access_token || "simulate_jwt_if_mocking"; 
      localStorage.setItem('daksha_token', token);

      toast.success("Welcome back!", {
        description: "Your cart has been merged successfully."
      });

      navigate('/dashboard');

    } catch (error) {
      console.error(error);
      toast.error("Authentication Failed", {
        description: error.response?.data?.detail || "Please check your number."
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 p-4">
      <Card className="w-[400px] shadow-lg border-t-4 border-blue-600">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">Daksha Retail</CardTitle>
          <CardDescription className="text-center">
            Enter your phone number to continue
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAuth} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input 
                id="phone" 
                placeholder="+91 99999 99999" 
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>
            
            {/* Mock OTP Field */}
            <div className="space-y-2">
              <Label htmlFor="otp">OTP (Verification)</Label>
              <Input 
                id="otp" 
                type="password"
                placeholder="123456" 
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
              />
            </div>

            <Button className="w-full bg-blue-600 hover:bg-blue-700" type="submit" disabled={loading}>
              {loading ? "Verifying..." : "Continue"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="justify-center text-sm text-muted-foreground">
          Secure Login • Powered by Team Rigged
        </CardFooter>
      </Card>
    </div>
  );
}