import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/apiClient";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function RegisterForm({ onSwitch }) {
  const { signUp } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    gender: "",
    date_of_birth: "",
    address_line: "",
    city: "",
    pincode: "",
    address_type: "home"
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSelectChange = (name, value) => {
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await signUp(formData.email, formData.password);

      const payload = {
        full_name: formData.full_name,
        gender: formData.gender,
        date_of_birth: formData.date_of_birth,
        preferred_languages: ["en"],
        address: {
          type: formData.address_type,
          address_line: formData.address_line,
          city: formData.city,
          pincode: formData.pincode
        }
      };

      await api.post("/auth/complete-profile", payload);
      
      navigate("/");
    } catch (error) {
      console.error("Registration failed:", error);
      alert(error.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader>
        <CardTitle>Create Account</CardTitle>
        <CardDescription>Enter your details to register.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          
          <div className="space-y-2">
            <Label>Email</Label>
            <Input name="email" type="email" required onChange={handleChange} />
          </div>

          <div className="space-y-2">
            <Label>Password</Label>
            <Input name="password" type="password" required onChange={handleChange} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input name="full_name" required onChange={handleChange} />
            </div>
            <div className="space-y-2">
              <Label>Date of Birth</Label>
              <Input name="date_of_birth" type="date" required onChange={handleChange} />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Gender</Label>
            <Select onValueChange={(val) => handleSelectChange("gender", val)}>
              <SelectTrigger>
                <SelectValue placeholder="Select Gender" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Address Line</Label>
            <Input name="address_line" placeholder="Street, Apt, etc." required onChange={handleChange} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>City</Label>
              <Input name="city" required onChange={handleChange} />
            </div>
            <div className="space-y-2">
              <Label>Pincode</Label>
              <Input name="pincode" required onChange={handleChange} />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Address Type</Label>
            <Select onValueChange={(val) => handleSelectChange("address_type", val)} defaultValue="home">
              <SelectTrigger>
                <SelectValue placeholder="Select Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="home">Home</SelectItem>
                <SelectItem value="work">Work</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating Account..." : "Register"}
          </Button>
          
          <div className="text-center text-sm mt-2">
            Already have an account?{" "}
            <span className="text-primary cursor-pointer hover:underline" onClick={onSwitch}>
              Login here
            </span>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}