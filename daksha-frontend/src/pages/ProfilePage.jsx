import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { UserService, LoyaltyService } from "../lib/api";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import {
  MapPin,
  CreditCard,
  Award,
  LogOut,
  Plus,
  Pencil,
  Sparkles,
  Send,
  Mail,
  ShieldCheck,
  Loader2,
  Trash2,
  User,
  Phone
} from "lucide-react";
import { toast } from "sonner";

export default function ProfilePage() {
  const { user, signOut } = useAuth();

  // --- Data State ---
  const [profile, setProfile] = useState(null);
  const [preferenceSummary, setPreferenceSummary] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [cards, setCards] = useState([]);
  const [points, setPoints] = useState(0);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // --- Modal States ---
  const [editOpen, setEditOpen] = useState(false);
  const [addressOpen, setAddressOpen] = useState(false);
  const [cardOpen, setCardOpen] = useState(false);

  // --- Forms ---
  const [draft, setDraft] = useState({ name: "", phone: "", gender: "" });
  
  const [newAddress, setNewAddress] = useState({
    label: "Home",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "",
    pincode: "",
    is_default: false
  });

  const [newCard, setNewCard] = useState({
    card_name: "",
    card_number: "",
    card_expiry: "", // MM/YY
    is_default: false
  });

  // ================= LOAD DATA =================
  const loadData = async () => {
    try {
      const [profRes, addrRes, cardRes, ptsRes] = await Promise.all([
        UserService.getProfile(),
        UserService.getAddresses(),
        UserService.getCards(),
        LoyaltyService.getPoints(),
      ]);

      // 1. Profile (Source of Truth is DB)
      const prof = profRes.data || profRes; 
      setProfile(prof);
      setDraft({
        name: prof.name || "",
        phone: prof.phone || "",
        gender: prof.gender || "",
      });

      // 2. Lists
      setAddresses(addrRes.data || addrRes || []);
      setCards(cardRes.data || cardRes || []);
      setPoints(ptsRes.data?.points || ptsRes.points || 0);

      // 3. Trigger Preference Recompute (Silent)
      UserService.recomputePreferences().catch(() => {});

    } catch (e) {
      console.error("Profile load error", e);
      toast.error("Failed to sync profile data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // ================= ACTIONS =================

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      // Filter out empty strings
      const payload = {};
      if (draft.name?.trim()) payload.name = draft.name.trim();
      if (draft.phone?.trim()) payload.phone = draft.phone.trim();
      if (draft.gender) payload.gender = draft.gender;

      await UserService.updateProfile(payload);
      
      // Reload to ensure UI matches DB
      const refreshed = await UserService.getProfile();
      setProfile(refreshed.data || refreshed);
      
      setEditOpen(false);
      toast.success("Profile updated");
    } catch (e) {
      toast.error("Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleAddAddress = async () => {
    // 1. Validation
    if (!newAddress.address_line1 || !newAddress.city || !newAddress.pincode || !newAddress.state) {
      toast.error("Please fill all required fields (Line 1, City, State, Pincode)");
      return;
    }

    setSaving(true);
    try {
      // 2. Construct Payload (Fix 422 Error)
      // We explicitly send null/empty string for optional fields to satisfy strict Pydantic schemas
      const payload = {
        label: newAddress.label || "Home",
        address_line1: newAddress.address_line1,
        address_line2: newAddress.address_line2 || null, // Send null if empty
        city: newAddress.city,
        state: newAddress.state,
        pincode: newAddress.pincode,
        country: "India",
        location: null, // Explicit null for GeoJSON field
        is_default: newAddress.is_default
      };

      await UserService.addAddress(payload);
      toast.success("Address added");
      
      // Refresh
      const res = await UserService.getAddresses();
      setAddresses(res.data || res);
      
      setAddressOpen(false);
      setNewAddress({ label: "Home", address_line1: "", address_line2: "", city: "", state: "", pincode: "", is_default: false });
    } catch (e) {
      console.error(e);
      toast.error("Failed to add address. Check format.");
    } finally {
      setSaving(false);
    }
  };

  const handleAddCard = async () => {
    if (!newCard.card_number || !newCard.card_expiry) {
      toast.error("Card details incomplete");
      return;
    }
    setSaving(true);
    try {
      await UserService.addCard(newCard);
      toast.success("Card added securely");

      const res = await UserService.getCards();
      setCards(res.data || res);
      
      setCardOpen(false);
      setNewCard({ card_name: "", card_number: "", card_expiry: "", is_default: false });
    } catch (e) {
      toast.error("Failed to add card");
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveCard = async (id) => {
    try {
      await UserService.removeCard(id);
      setCards(prev => prev.filter(c => c.id !== id));
      toast.success("Card removed");
    } catch (e) {
      toast.error("Could not remove card");
    }
  };

  const telegramLink = profile?.id ? `https://t.me/daksha_retail_bot?start=${profile.id}` : "#";

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-8 p-6">
        <Skeleton className="h-40 w-full rounded-2xl" />
        <div className="grid md:grid-cols-2 gap-6">
          <Skeleton className="h-64 rounded-2xl" />
          <Skeleton className="h-64 rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-10 animate-in fade-in duration-500 pb-20">
      
      {/* ================= HEADER ================= */}
      <div className="flex flex-col md:flex-row items-center md:items-start gap-8 bg-white p-8 rounded-3xl border border-zinc-100 shadow-sm">
        <div className="relative">
          <Avatar className="h-32 w-32 border-4 border-white shadow-xl bg-zinc-100">
            <AvatarFallback className="bg-black text-white text-4xl font-serif">
              {profile?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="absolute bottom-2 right-2 bg-emerald-500 w-5 h-5 rounded-full border-4 border-white" title="Active" />
        </div>
        
        <div className="flex-1 text-center md:text-left space-y-3">
          <div>
            <h1 className="text-4xl font-serif font-bold text-zinc-900 tracking-tight">
              {profile?.name || "Member"}
            </h1>
            <div className="flex flex-col md:flex-row items-center md:items-start gap-2 md:gap-4 text-zinc-500 mt-2 text-sm">
              <span className="flex items-center gap-1.5"><Mail size={14} /> {profile?.email}</span>
              {profile?.phone && <span className="flex items-center gap-1.5"><Phone size={14} /> {profile.phone}</span>}
            </div>
          </div>

          <div className="flex flex-wrap justify-center md:justify-start gap-3 pt-2">
            <Badge variant="secondary" className="px-4 py-1.5 bg-zinc-100 text-zinc-800 rounded-full gap-2">
              <Award size={14} className="text-amber-600" />
              <span className="font-bold">{points}</span> Points
            </Badge>
            <Badge variant="outline" className="px-4 py-1.5 border-zinc-200 text-zinc-600 uppercase tracking-widest text-[10px]">
              {profile?.loyalty_tier || "Silver"} Tier
            </Badge>
          </div>
        </div>

        {/* Edit Button */}
        <Dialog open={editOpen} onOpenChange={setEditOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="rounded-full px-6 border-zinc-200 hover:bg-zinc-50 hover:border-zinc-300 transition-all">
              <Pencil size={14} className="mr-2" /> Edit Profile
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle className="font-serif text-2xl">Edit Profile</DialogTitle>
              <DialogDescription>Update your personal information.</DialogDescription>
            </DialogHeader>
            <div className="grid gap-5 py-4">
              <div className="space-y-2">
                <Label>Full Name</Label>
                <Input value={draft.name} onChange={e => setDraft({...draft, name: e.target.value})} placeholder="Your Name" />
              </div>
              <div className="space-y-2">
                <Label>Phone Number</Label>
                <Input value={draft.phone} onChange={e => setDraft({...draft, phone: e.target.value})} placeholder="+91..." />
              </div>
              <div className="space-y-2">
                <Label>Gender</Label>
                <Select value={draft.gender} onValueChange={(val) => setDraft({...draft, gender: val})}>
                  <SelectTrigger><SelectValue placeholder="Select Gender" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="unisex">Unisex</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleSaveProfile} disabled={saving} className="w-full h-11 rounded-lg bg-black text-white hover:bg-zinc-800">
                {saving ? <Loader2 className="animate-spin mr-2 h-4 w-4"/> : "Save Changes"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="account" className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px] mb-8 bg-zinc-100/50 p-1 rounded-full">
          <TabsTrigger value="account" className="rounded-full data-[state=active]:bg-white data-[state=active]:shadow-sm">Account</TabsTrigger>
          <TabsTrigger value="wallet" className="rounded-full data-[state=active]:bg-white data-[state=active]:shadow-sm">Wallet & Cards</TabsTrigger>
        </TabsList>

        {/* --- TAB: ACCOUNT --- */}
        <TabsContent value="account" className="space-y-8 animate-in slide-in-from-left-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            {/* Style DNA */}
            <Card className="bg-gradient-to-br from-zinc-50 to-white border-zinc-200 overflow-hidden relative group hover:shadow-md transition-all">
              <div className="absolute top-4 right-4 text-zinc-200 group-hover:text-zinc-300 transition-colors">
                <Sparkles size={80} strokeWidth={1} />
              </div>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-serif text-xl">
                  Style DNA
                </CardTitle>
                <CardDescription>Your AI-generated fashion profile</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-zinc-600 text-sm leading-relaxed italic relative z-10">
                  "{preferenceSummary?.summary_text || "We are currently analyzing your shopping patterns to curate a personalized boutique just for you."}"
                </p>
              </CardContent>
            </Card>

            {/* Telegram Concierge */}
            <Card className="border-zinc-200 hover:shadow-md transition-all">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 font-serif text-xl">
                  Concierge
                </CardTitle>
                <CardDescription>Connect via Telegram for instant 24/7 support.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild className="w-full h-12 rounded-xl bg-[#24A1DE] hover:bg-[#1E8BBF] text-white shadow-lg shadow-blue-500/20">
                  <a href={telegramLink} target="_blank" rel="noreferrer">
                    <Send size={18} className="mr-2" /> Connect Telegram Bot
                  </a>
                </Button>
              </CardContent>
            </Card>

            {/* Address Book */}
            <Card className="border-zinc-200 md:col-span-2">
              <CardHeader className="flex flex-row items-center justify-between border-b border-zinc-50 pb-4">
                <div>
                  <CardTitle className="font-serif text-xl">Address Book</CardTitle>
                  <CardDescription>Manage your shipping destinations</CardDescription>
                </div>
                <Dialog open={addressOpen} onOpenChange={setAddressOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="rounded-full gap-2">
                      <Plus size={14} /> Add New
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader><DialogTitle>New Address</DialogTitle></DialogHeader>
                    <div className="grid gap-4 py-4">
                      <div className="space-y-2">
                        <Label>Label</Label>
                        <Input value={newAddress.label} onChange={e => setNewAddress({...newAddress, label: e.target.value})} placeholder="e.g. Home, Office" />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Address Line 1</Label>
                          <Input value={newAddress.address_line1} onChange={e => setNewAddress({...newAddress, address_line1: e.target.value})} placeholder="Street, Sector" />
                        </div>
                        <div className="space-y-2">
                          <Label>Address Line 2 (Optional)</Label>
                          <Input value={newAddress.address_line2} onChange={e => setNewAddress({...newAddress, address_line2: e.target.value})} placeholder="Apt, Suite" />
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label>City</Label>
                          <Input value={newAddress.city} onChange={e => setNewAddress({...newAddress, city: e.target.value})} />
                        </div>
                        <div className="space-y-2">
                          <Label>State</Label>
                          <Input value={newAddress.state} onChange={e => setNewAddress({...newAddress, state: e.target.value})} />
                        </div>
                        <div className="space-y-2">
                          <Label>Pincode</Label>
                          <Input value={newAddress.pincode} onChange={e => setNewAddress({...newAddress, pincode: e.target.value})} />
                        </div>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button onClick={handleAddAddress} disabled={saving} className="w-full bg-black text-white">{saving ? "Saving..." : "Save Address"}</Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent className="pt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                {addresses.length === 0 ? (
                  <div className="col-span-full py-8 text-center text-zinc-400 bg-zinc-50/50 rounded-xl border border-dashed border-zinc-200">
                    <MapPin className="mx-auto h-8 w-8 mb-2 opacity-50" />
                    <p>No addresses saved yet.</p>
                  </div>
                ) : (
                  addresses.map((addr) => (
                    <div key={addr.id} className="relative p-4 rounded-xl border border-zinc-100 bg-white hover:border-zinc-300 transition-all shadow-sm group">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-zinc-900">{addr.label}</span>
                          {addr.is_default && <Badge variant="secondary" className="text-[10px] h-5 px-1.5">Default</Badge>}
                        </div>
                        <MapPin size={14} className="text-zinc-400 group-hover:text-black transition-colors" />
                      </div>
                      <p className="text-xs text-zinc-500 leading-relaxed">
                        {addr.address_line1} {addr.address_line2 && `, ${addr.address_line2}`}<br />
                        {addr.city}, {addr.state} - {addr.pincode}
                      </p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* --- TAB: WALLET --- */}
        <TabsContent value="wallet" className="animate-in slide-in-from-right-4 duration-500">
          <Card className="border-zinc-200">
            <CardHeader className="flex flex-row items-center justify-between border-b border-zinc-50 pb-4">
              <div>
                <CardTitle className="font-serif text-xl">Saved Cards</CardTitle>
                <CardDescription>Securely manage your payment methods</CardDescription>
              </div>
              <Dialog open={cardOpen} onOpenChange={setCardOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="rounded-full gap-2">
                    <Plus size={14} /> Add Card
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader><DialogTitle>Add New Card</DialogTitle></DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                      <Label>Cardholder Name</Label>
                      <Input value={newCard.card_name} onChange={e => setNewCard({...newCard, card_name: e.target.value})} placeholder="Name on card" />
                    </div>
                    <div className="space-y-2">
                      <Label>Card Number</Label>
                      <Input value={newCard.card_number} onChange={e => setNewCard({...newCard, card_number: e.target.value})} maxLength={19} placeholder="0000 0000 0000 0000" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Expiry</Label>
                        <Input value={newCard.card_expiry} onChange={e => setNewCard({...newCard, card_expiry: e.target.value})} placeholder="MM/YY" maxLength={5} />
                      </div>
                      <div className="space-y-2">
                        <Label>CVV</Label>
                        <Input type="password" maxLength={3} placeholder="***" disabled className="bg-zinc-50" />
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button onClick={handleAddCard} disabled={saving} className="w-full bg-black text-white">{saving ? "Saving..." : "Save Card"}</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {cards.length === 0 ? (
                  <div className="col-span-full py-12 text-center text-zinc-400 bg-zinc-50/50 rounded-xl border border-dashed border-zinc-200">
                    <ShieldCheck className="mx-auto h-10 w-10 mb-3 opacity-50" />
                    <p>No payment methods saved.</p>
                  </div>
                ) : (
                  cards.map((card) => (
                    <div key={card.id} className="relative overflow-hidden p-5 rounded-2xl bg-zinc-900 text-zinc-300 shadow-xl group hover:scale-[1.02] transition-transform duration-300">
                      <div className="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
                        <CreditCard size={80} />
                      </div>
                      
                      <div className="flex justify-between items-start mb-6">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 font-bold">Daksha Secure</p>
                        <button onClick={() => handleRemoveCard(card.id)} className="text-zinc-600 hover:text-red-400 transition-colors bg-white/5 p-1.5 rounded-full backdrop-blur-sm">
                          <Trash2 size={12} />
                        </button>
                      </div>
                      
                      <p className="font-mono text-xl text-white mb-6 tracking-wider">
                        •••• •••• •••• {card.card_number.slice(-4)}
                      </p>
                      
                      <div className="flex justify-between items-end text-xs font-medium">
                        <div>
                          <p className="text-zinc-600 text-[9px] uppercase mb-0.5">Card Holder</p>
                          <span className="uppercase text-zinc-200">{card.card_name}</span>
                        </div>
                        <div className="text-right">
                          <p className="text-zinc-600 text-[9px] uppercase mb-0.5">Expires</p>
                          <span className="text-zinc-200">{card.card_expiry}</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* --- FOOTER --- */}
      <div className="pt-12 border-t border-zinc-100 flex justify-center">
        <Button 
          variant="ghost" 
          onClick={signOut}
          className="text-red-600 hover:text-red-700 hover:bg-red-50 gap-2 px-6"
        >
          <LogOut size={16} /> Sign Out
        </Button>
      </div>
    </div>
  );
}