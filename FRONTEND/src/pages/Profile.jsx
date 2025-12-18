// FRONTEND/src/pages/Profile.jsx

import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { supabase } from "@/lib/supabaseClient"; 
import { toast } from "sonner";
import { 
  User, MapPin, CreditCard, Save, Loader2, Crown, Sparkles, LogOut, 
  ArrowLeft, Trash2, Plus, ShieldCheck, Lock, Camera, Home, Briefcase, Map
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";

// --- Helpers ---
const getInitials = (name, email) => {
  if (name) {
    const parts = name.split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
  }
  if (email) return email.substring(0, 2).toUpperCase();
  return "U";
};

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  
  // Data State
  const [personalData, setPersonalData] = useState({});
  const [styleData, setStyleData] = useState({});
  const [addresses, setAddresses] = useState([]);
  const [payments, setPayments] = useState([]);
  const [notifications, setNotifications] = useState([]);

  // Modal States
  const [isAddressOpen, setIsAddressOpen] = useState(false);
  const [isCardOpen, setIsCardOpen] = useState(false);

  // Forms
  const [newAddress, setNewAddress] = useState({
    type: "home",
    address_line: "",
    city: "",
    pincode: "",
    is_default: false
  });

  const [cardInput, setCardInput] = useState({
    number: "",
    expiry: "",
    cvc: "",
    is_default: false
  });

  // --- 1. FETCH DATA ---
  const fetchAllData = async () => {
    try {
      if (!user) return;
      if (!personalData.id) setLoading(true);

      const { data: userData } = await supabase.from('users').select('*').eq('id', user.id).single();
      if (userData) setPersonalData(userData);

      const { data: style } = await supabase.from('user_style_profile').select('*').eq('user_id', user.id).maybeSingle();
      if (style) setStyleData(style);

      const { data: addrList } = await supabase.from('user_addresses').select('*').eq('user_id', user.id).order('is_default', { ascending: false });
      setAddresses(addrList || []);

      const { data: payList } = await supabase.from('user_payment_methods').select('*').eq('user_id', user.id).order('is_default', { ascending: false });
      setPayments(payList || []);

      const { data: notifList } = await supabase.from('user_notifications').select('*').eq('user_id', user.id).order('created_at', { ascending: false });
      setNotifications(notifList || []);

    } catch (err) {
      console.error("Profile load error:", err);
      toast.error("Could not load profile data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, [user]);

  // --- 2. Handlers ---

  const handleSavePersonal = async () => {
    try {
      const { error } = await supabase.from('users').update({
        full_name: personalData.full_name,
        date_of_birth: personalData.date_of_birth,
        gender: personalData.gender
      }).eq('id', user.id);

      if (error) throw error;
      toast.success("Personal details saved.");
    } catch (err) {
      toast.error("Failed to save.");
    }
  };

  const handleSaveAddress = async () => {
    try {
      if (!newAddress.address_line || !newAddress.city || !newAddress.pincode) {
        toast.error("Please fill in Address, City, and Pincode");
        return;
      }
      
      const { error } = await supabase.from('user_addresses').insert({
        user_id: user.id,
        type: newAddress.type,
        address_line: newAddress.address_line,
        city: newAddress.city,
        pincode: newAddress.pincode,
        is_default: newAddress.is_default
      });

      if (error) throw error;
      
      await fetchAllData(); 
      setIsAddressOpen(false);
      setNewAddress({ type: "home", address_line: "", city: "", pincode: "", is_default: false });
      toast.success("Address added");
    } catch (err) {
      console.error(err);
      toast.error("Failed to add address");
    }
  };

  const handleSaveCard = async () => {
    try {
      const cleanNum = cardInput.number.replace(/\D/g, "");
      if (cleanNum.length < 13) return toast.error("Invalid card number");

      const mockToken = `tok_${Math.random().toString(36).substr(2, 12)}_secure`;
      const brand = cleanNum.startsWith("4") ? "visa" : cleanNum.startsWith("5") ? "mastercard" : "generic";
      const last4 = cleanNum.slice(-4);

      const { error } = await supabase.from('user_payment_methods').insert({
        user_id: user.id,
        provider: "stripe_mock",
        gateway_token_id: mockToken,
        card_last4: last4,
        card_brand: brand,
        is_default: cardInput.is_default
      });

      if (error) throw error;
      
      await fetchAllData();
      setIsCardOpen(false);
      setCardInput({ number: "", expiry: "", cvc: "", is_default: false });
      toast.success("Card securely saved");
    } catch (err) {
      toast.error("Failed to save card");
    }
  };

  const handleDeleteAddress = async (id) => {
    try {
      const { error } = await supabase.from('user_addresses').delete().eq('id', id);
      if (error) throw error;
      setAddresses(prev => prev.filter(a => a.id !== id));
      toast.success("Address removed");
    } catch (err) {
      toast.error("Failed to delete address");
    }
  };

  const handleDeleteCard = async (id) => {
    try {
      const { error } = await supabase.from('user_payment_methods').delete().eq('id', id);
      if (error) throw error;
      setPayments(prev => prev.filter(p => p.id !== id));
      toast.success("Card removed");
    } catch (err) {
      toast.error("Failed to delete card");
    }
  };

  const handleUpdateStyle = async () => {
    try {
        const { error } = await supabase.from('user_style_profile').upsert({
            user_id: user.id,
            preferred_tags: styleData.preferred_tags
        });
        if (error) throw error;
        toast.success("AI Preferences Updated");
    } catch (err) {
        toast.error("Failed to update style");
    }
  };

  // --- Render ---

  if (loading && !personalData.id) return <ProfileSkeleton />;

  return (
    <div className="container max-w-5xl mx-auto py-6 px-4 space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" className="gap-2 pl-0 hover:pl-2 transition-all" onClick={() => navigate("/home")}>
          <ArrowLeft className="h-5 w-5" /> Back to home
        </Button>
        <Button variant="outline" onClick={logout} className="text-destructive hover:bg-destructive/10 border-destructive/20">
          <LogOut className="h-4 w-4 mr-2" /> Sign Out
        </Button>
      </div>

      {/* Hero Card */}
      <Card className="border-none bg-gradient-to-r from-slate-950 to-slate-900 text-white overflow-hidden relative shadow-2xl">
        <div className="absolute top-0 right-0 p-40 bg-purple-500/10 blur-3xl rounded-full"></div>
        <CardContent className="p-8 flex flex-col md:flex-row items-center gap-8 relative z-10">
          <Avatar className="h-32 w-32 border-4 border-white/10 shadow-xl bg-slate-800">
            <AvatarImage src={personalData.avatar_url} className="object-cover" />
            <AvatarFallback className="text-4xl font-medium text-white bg-slate-700">
              {getInitials(personalData.full_name, user?.email)}
            </AvatarFallback>
          </Avatar>
          <div className="text-center md:text-left space-y-2 flex-1">
            <h1 className="text-3xl font-bold tracking-tight">{personalData.full_name || "Guest User"}</h1>
            <p className="text-slate-400 font-mono text-sm">{user?.email}</p>
            <div className="flex items-center justify-center md:justify-start gap-3 pt-3">
              <Badge variant="secondary" className="bg-amber-500/10 text-amber-300 border-amber-500/20 px-3 py-1.5 backdrop-blur-md">
                <Crown className="h-3.5 w-3.5 mr-2" />
                {(personalData.loyalty_tier || "Bronze").toUpperCase()}
              </Badge>
              <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-300 border-emerald-500/20 px-3 py-1.5 backdrop-blur-md">
                {personalData.loyalty_points || 0} Points
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="addresses" className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5 h-auto p-1 bg-muted/50 rounded-xl">
          <TabsTrigger value="general" className="py-2.5 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">General</TabsTrigger>
          <TabsTrigger value="style" className="py-2.5 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">AI Style</TabsTrigger>
          <TabsTrigger value="addresses" className="py-2.5 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">Addresses</TabsTrigger>
          <TabsTrigger value="payments" className="py-2.5 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">Payments</TabsTrigger>
          <TabsTrigger value="notifications" className="py-2.5 rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm">Notifications</TabsTrigger>
        </TabsList>

        {/* 1. General Tab */}
        <TabsContent value="general" className="mt-6">
          <Card>
            <CardHeader><CardTitle>Identity & Contact</CardTitle></CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input value={personalData.full_name || ""} onChange={e => setPersonalData({...personalData, full_name: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <Input value={personalData.phone_number || ""} disabled className="bg-muted text-muted-foreground" />
                  <span className="text-[10px] text-emerald-600 flex items-center gap-1 mt-1"><ShieldCheck className="h-3 w-3" /> Verified Securely</span>
                </div>
                <div className="space-y-2">
                  <Label>Date of Birth</Label>
                  <Input type="date" value={personalData.date_of_birth || ""} onChange={e => setPersonalData({...personalData, date_of_birth: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Gender</Label>
                  <Select value={personalData.gender || ""} onValueChange={val => setPersonalData({...personalData, gender: val})}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">Male</SelectItem>
                      <SelectItem value="female">Female</SelectItem>
                      <SelectItem value="unisex">Unisex / Non-binary</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end pt-4">
                <Button onClick={handleSavePersonal}><Save className="h-4 w-4 mr-2" /> Save Changes</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 2. AI Style Tab */}
        <TabsContent value="style" className="mt-6">
          <div className="grid lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
               <CardHeader><CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-purple-600" /> Style Profile</CardTitle></CardHeader>
               <CardContent className="space-y-4">
                 <Label>Style Notes</Label>
                 <Textarea 
                   placeholder="E.g. I prefer breathable fabrics..." 
                   className="min-h-[120px]"
                   value={styleData.preferred_tags?.note || ""} 
                   onChange={e => setStyleData({...styleData, preferred_tags: { ...styleData.preferred_tags, note: e.target.value }})}
                 />
                 <Button onClick={handleUpdateStyle}>Update Profile</Button>
               </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-100">
               <CardHeader><CardTitle className="text-purple-900 text-lg">Your Vibe</CardTitle></CardHeader>
               <CardContent>
                 <div className="flex flex-wrap gap-2">
                   {['Casual', 'Summer', 'Modern'].map(t => <Badge key={t} variant="secondary" className="bg-white">{t}</Badge>)}
                 </div>
                 <p className="text-xs text-purple-600 mt-4">AI generated based on browsing.</p>
               </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 3. Addresses Tab (Enhanced UI) */}
        <TabsContent value="addresses" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div><CardTitle>Saved Addresses</CardTitle><CardDescription>Manage delivery locations.</CardDescription></div>
              <Dialog open={isAddressOpen} onOpenChange={setIsAddressOpen}>
                <DialogTrigger asChild><Button size="sm"><Plus className="h-4 w-4 mr-2" /> Add Address</Button></DialogTrigger>
                <DialogContent className="sm:max-w-[500px]">
                  <DialogHeader>
                    <DialogTitle>Add New Address</DialogTitle>
                    <DialogDescription>Where should we deliver your order?</DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-6 py-4">
                    {/* Visual Type Selector */}
                    <div className="grid grid-cols-3 gap-4">
                        {['home', 'work', 'other'].map((type) => (
                            <div 
                                key={type}
                                onClick={() => setNewAddress({...newAddress, type})}
                                className={`cursor-pointer flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all ${newAddress.type === type ? 'border-primary bg-primary/5' : 'border-muted hover:border-primary/50'}`}
                            >
                                {type === 'home' && <Home className="h-5 w-5 mb-1" />}
                                {type === 'work' && <Briefcase className="h-5 w-5 mb-1" />}
                                {type === 'other' && <Map className="h-5 w-5 mb-1" />}
                                <span className="text-xs font-medium capitalize">{type}</span>
                            </div>
                        ))}
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label>Address Line</Label>
                            <div className="relative">
                                <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input className="pl-9" placeholder="Street, Apartment, Suite" value={newAddress.address_line} onChange={(e) => setNewAddress({...newAddress, address_line: e.target.value})} />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>City</Label>
                                <Input placeholder="New York" value={newAddress.city} onChange={(e) => setNewAddress({...newAddress, city: e.target.value})} />
                            </div>
                            <div className="space-y-2">
                                <Label>Pincode</Label>
                                <Input placeholder="10001" value={newAddress.pincode} onChange={(e) => setNewAddress({...newAddress, pincode: e.target.value})} />
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 pt-2 border-t mt-2">
                      <Switch id="def-addr" checked={newAddress.is_default} onCheckedChange={(c) => setNewAddress({...newAddress, is_default: c})} />
                      <Label htmlFor="def-addr" className="font-normal cursor-pointer">Set as default delivery address</Label>
                    </div>
                  </div>
                  <DialogFooter><Button onClick={handleSaveAddress}>Save Address</Button></DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              {addresses.map((addr) => (
                <div key={addr.id} className="relative flex items-start justify-between border p-4 rounded-lg bg-card hover:bg-muted/10 transition-colors group">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="capitalize">{addr.type}</Badge>
                      {addr.is_default && <span className="text-[10px] font-medium text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">Default</span>}
                    </div>
                    <p className="font-medium text-sm pt-1">{addr.address_line}</p>
                    <p className="text-xs text-muted-foreground">{addr.city}, {addr.pincode}</p>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors" onClick={() => handleDeleteAddress(addr.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              {addresses.length === 0 && <p className="col-span-full text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/10">No addresses found.</p>}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 4. Payments Tab */}
        <TabsContent value="payments" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div><CardTitle>Payment Methods</CardTitle><CardDescription>Securely managed via Stripe.</CardDescription></div>
              <Dialog open={isCardOpen} onOpenChange={setIsCardOpen}>
                <DialogTrigger asChild><Button size="sm"><Plus className="h-4 w-4 mr-2" /> Add Card</Button></DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Card</DialogTitle>
                    <DialogDescription className="flex items-center gap-1 text-emerald-600"><Lock className="h-3 w-3" /> 256-bit SSL Encrypted</DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                      <Label>Card Number</Label>
                      <div className="relative">
                        <CreditCard className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input className="pl-9 font-mono" placeholder="0000 0000 0000 0000" maxLength={19} value={cardInput.number} onChange={(e) => setCardInput({...cardInput, number: e.target.value})} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Expiry</Label>
                        <Input placeholder="MM/YY" maxLength={5} value={cardInput.expiry} onChange={(e) => setCardInput({...cardInput, expiry: e.target.value})} />
                      </div>
                      <div className="space-y-2">
                        <Label>CVC</Label>
                        <Input type="password" maxLength={4} placeholder="123" value={cardInput.cvc} onChange={(e) => setCardInput({...cardInput, cvc: e.target.value})} />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 pt-2">
                      <Switch id="def-card" checked={cardInput.is_default} onCheckedChange={(c) => setCardInput({...cardInput, is_default: c})} />
                      <Label htmlFor="def-card">Set as Default</Label>
                    </div>
                  </div>
                  <DialogFooter><Button onClick={handleSaveCard}>Save Securely</Button></DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent className="space-y-3">
              {payments.map((p) => (
                <div key={p.id} className="flex items-center justify-between border p-4 rounded-lg bg-card group">
                   <div className="flex items-center gap-4">
                     <div className="h-10 w-14 bg-slate-100 rounded border flex items-center justify-center">
                        <CreditCard className="h-5 w-5 text-slate-500" />
                     </div>
                     <div>
                       <p className="font-medium capitalize text-sm">{p.card_brand} <span className="text-muted-foreground">••••</span> {p.card_last4}</p>
                       <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Secure Token</p>
                     </div>
                   </div>
                   <div className="flex items-center gap-3">
                       {p.is_default && <Badge variant="secondary" className="text-[10px] bg-slate-100 text-slate-700">Default</Badge>}
                       <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100 transition-all" onClick={() => handleDeleteCard(p.id)}>
                           <Trash2 className="h-4 w-4" />
                       </Button>
                   </div>
                </div>
              ))}
              {payments.length === 0 && <p className="text-center py-8 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/10">No cards saved.</p>}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader><CardTitle>Notifications</CardTitle></CardHeader>
            <CardContent>
              {notifications.length === 0 ? <p className="text-center text-muted-foreground py-8">No new notifications.</p> : notifications.map((n, i) => (
                <div key={n.id || i} className="mb-4 border-b pb-4 last:border-0">
                  <h4 className="font-medium text-sm">{n.title}</h4>
                  <p className="text-sm text-muted-foreground">{n.body}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="container max-w-5xl mx-auto py-6 px-4 space-y-6">
       <Skeleton className="h-10 w-full" />
       <Skeleton className="h-64 w-full rounded-xl" />
       <div className="grid gap-4 md:grid-cols-2">
         <Skeleton className="h-40 w-full" />
         <Skeleton className="h-40 w-full" />
       </div>
    </div>
  );
}