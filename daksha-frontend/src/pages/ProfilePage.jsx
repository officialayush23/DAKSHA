import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { UserService, LoyaltyService, apiRequest } from "../lib/api";

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
  Phone,
  Gift,
  Tag
} from "lucide-react";
import { toast } from "sonner";

export default function ProfilePage() {
  const { user, signOut } = useAuth();

  // --- Data State ---
  const [profile, setProfile] = useState(null);
  const [preferenceSummary, setPreferenceSummary] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [cards, setCards] = useState([]);
  const [offers, setOffers] = useState([]);
  const [points, setPoints] = useState(0);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // --- Modal States ---
  const [editOpen, setEditOpen] = useState(false);
  const [addressOpen, setAddressOpen] = useState(false);
  const [cardOpen, setCardOpen] = useState(false);

  // --- Forms ---
  const [draft, setDraft] = useState({ 
    name: "", 
    phone: "", 
    gender: "",
    preferences: { preferred_sizes: "", preferred_colors: "", preferred_categories: "" } 
  });
  
  const [newAddress, setNewAddress] = useState({
    label: "Home",
    address_line1: "",
    address_line2: "",
    city: "",
    state: "",
    pincode: "",
    is_default: false
  });

  // UPDATED: Mapped exactly to Pydantic Schema requirements
  const [newCard, setNewCard] = useState({
    card_name: "",
    card_brand: "",
    card_last4: "", 
    token: "",
    is_default: false
  });

  // ================= LOAD DATA =================
  const loadData = async () => {
    try {
      // Parallel API fetching
      const [profRes, addrRes, cardRes, ptsRes, offersRes] = await Promise.all([
        UserService.getProfile(),
        UserService.getAddresses(),
        UserService.getCards(),
        LoyaltyService.getSummary().catch(() => ({ data: { points: 0 }})),
        UserService.getOffers().catch(() => ({ data: { offers: [] }})),
      ]);

      const prof = profRes.data || profRes; 
      setProfile(prof);
      
      setDraft({
        name: prof.name || "",
        phone: prof.phone || "",
        gender: prof.gender || "",
        preferences: {
          preferred_sizes: prof.preferences?.preferred_sizes?.join(", ") || "",
          preferred_colors: prof.preferences?.preferred_colors?.join(", ") || "",
          preferred_categories: prof.preferences?.preferred_categories?.join(", ") || ""
        }
      });

      setAddresses(addrRes.data || addrRes || []);
      setCards(cardRes.data || cardRes || []);
      setOffers(offersRes.data?.offers || offersRes?.offers || []);
      
      const fetchedPoints = ptsRes.data?.points || ptsRes?.points || ptsRes?.data?.total_points || 0;
      setPoints(prof.points_balance !== undefined ? prof.points_balance : fetchedPoints);

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
      const parseToArray = (str) => str ? str.split(',').map(s => s.trim()).filter(Boolean) : [];

      const payload = {
        name: draft.name?.trim() || undefined,
        phone: draft.phone?.trim() || undefined,
        gender: draft.gender || undefined,
        preferences: {
          preferred_sizes: parseToArray(draft.preferences.preferred_sizes),
          preferred_colors: parseToArray(draft.preferences.preferred_colors),
          preferred_categories: parseToArray(draft.preferences.preferred_categories)
        }
      };

      await UserService.updateProfile(payload);
      
      const refreshed = await UserService.getProfile();
      setProfile(refreshed.data || refreshed);
      
      setEditOpen(false);
      toast.success("Profile & Preferences updated");
    } catch (e) {
      toast.error("Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleAddAddress = async () => {
    if (!newAddress.address_line1 || !newAddress.city || !newAddress.pincode || !newAddress.state) {
      toast.error("Please fill all required fields");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        label: newAddress.label || "Home",
        address_line1: newAddress.address_line1,
        address_line2: newAddress.address_line2 || null,
        city: newAddress.city,
        state: newAddress.state,
        pincode: newAddress.pincode,
        country: "India",
        location: null,
        is_default: newAddress.is_default
      };

      await UserService.addAddress(payload);
      toast.success("Address added");
      
      const res = await UserService.getAddresses();
      setAddresses(res.data || res);
      
      setAddressOpen(false);
      setNewAddress({ label: "Home", address_line1: "", address_line2: "", city: "", state: "", pincode: "", is_default: false });
    } catch (e) {
      toast.error("Failed to add address.");
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveAddress = async (id) => {
    try {
      await apiRequest(`/user/addresses/${id}`, { method: 'DELETE' });
      setAddresses(prev => prev.filter(a => a.id !== id));
      toast.success("Address removed");
    } catch (e) {
      toast.error("Could not remove address");
    }
  };

  const handleAddCard = async () => {
    // UPDATED Validation: Check exact fields
    if (!newCard.card_name || !newCard.card_brand || !newCard.token) {
      toast.error("Please fill all fields.");
      return;
    }
    
    if (newCard.card_last4.length !== 4) {
      toast.error("Last 4 digits must be exactly 4 characters.");
      return;
    }

    setSaving(true);
    try {
      // Direct pass-through of the exact fields required by schema
      const payload = {
        card_brand: newCard.card_brand,
        card_last4: newCard.card_last4,
        token: newCard.token,
        card_name: newCard.card_name,
        is_default: newCard.is_default
      };

      await UserService.addCard(payload);
      toast.success("Card securely linked");

      const res = await UserService.getCards();
      setCards(res.data || res);
      
      setCardOpen(false);
      // Reset form
      setNewCard({ card_name: "", card_brand: "", card_last4: "", token: "", is_default: false });
    } catch (e) {
      toast.error("Failed to add card. Verify inputs match schema requirements.");
      console.error(e);
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

        {/* Edit Profile Button & Dialog */}
        <Dialog open={editOpen} onOpenChange={setEditOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="rounded-full px-6 border-zinc-200 hover:bg-zinc-50 hover:border-zinc-300 transition-all">
              <Pencil size={14} className="mr-2" /> Edit Profile
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="font-serif text-2xl">Edit Profile</DialogTitle>
              <DialogDescription>Update your personal information and style preferences.</DialogDescription>
            </DialogHeader>
            <div className="grid gap-5 py-4 max-h-[60vh] overflow-y-auto px-1">
              
              <div className="space-y-2">
                <Label>Full Name</Label>
                <Input value={draft.name} onChange={e => setDraft({...draft, name: e.target.value})} placeholder="Your Name" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <Input value={draft.phone} onChange={e => setDraft({...draft, phone: e.target.value})} placeholder="+91..." />
                </div>
                <div className="space-y-2">
                  <Label>Gender</Label>
                  <Select value={draft.gender} onValueChange={(val) => setDraft({...draft, gender: val})}>
                    <SelectTrigger><SelectValue placeholder="Select Gender" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Male">Male</SelectItem>
                      <SelectItem value="Female">Female</SelectItem>
                      <SelectItem value="Unisex">Unisex</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="border-t border-zinc-100 my-2" />

              <div className="space-y-2">
                <Label>Preferred Sizes <span className="text-xs text-zinc-400 font-normal">(comma separated)</span></Label>
                <Input value={draft.preferences.preferred_sizes} onChange={e => setDraft({...draft, preferences: {...draft.preferences, preferred_sizes: e.target.value}})} placeholder="S, M, L, 9, 10" />
              </div>
              <div className="space-y-2">
                <Label>Favorite Colors</Label>
                <Input value={draft.preferences.preferred_colors} onChange={e => setDraft({...draft, preferences: {...draft.preferences, preferred_colors: e.target.value}})} placeholder="Black, Navy, White" />
              </div>
              <div className="space-y-2">
                <Label>Preferred Categories</Label>
                <Input value={draft.preferences.preferred_categories} onChange={e => setDraft({...draft, preferences: {...draft.preferences, preferred_categories: e.target.value}})} placeholder="Sneakers, Jackets" />
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
        <TabsList className="grid w-full grid-cols-3 lg:w-[500px] mb-8 bg-zinc-100/50 p-1 rounded-full">
          <TabsTrigger value="account" className="rounded-full data-[state=active]:bg-white data-[state=active]:shadow-sm">Account</TabsTrigger>
          <TabsTrigger value="rewards" className="rounded-full data-[state=active]:bg-white data-[state=active]:shadow-sm">Rewards</TabsTrigger>
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
              <CardContent className="space-y-4">
                <p className="text-zinc-600 text-sm leading-relaxed italic relative z-10">
                  "{preferenceSummary?.summary_text || "We are currently analyzing your shopping patterns to curate a personalized boutique just for you."}"
                </p>
                <div className="relative z-10 space-y-3 pt-2">
                  {profile?.preferences?.preferred_sizes?.length > 0 && (
                    <div>
                      <p className="text-xs uppercase font-bold tracking-wider text-zinc-400 mb-2">Sizes</p>
                      <div className="flex flex-wrap gap-2">
                        {profile.preferences.preferred_sizes.map(s => (
                          <Badge key={s} variant="outline" className="bg-white">{s}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {profile?.preferences?.preferred_colors?.length > 0 && (
                    <div>
                      <p className="text-xs uppercase font-bold tracking-wider text-zinc-400 mb-2">Colors</p>
                      <div className="flex flex-wrap gap-2">
                        {profile.preferences.preferred_colors.map(c => (
                          <Badge key={c} variant="outline" className="bg-white">{c}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
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
                        <button onClick={() => handleRemoveAddress(addr.id)} className="text-zinc-400 hover:text-red-500 transition-colors p-1 rounded-md">
                          <Trash2 size={16} />
                        </button>
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

        {/* --- TAB: REWARDS & OFFERS --- */}
        <TabsContent value="rewards" className="animate-in slide-in-from-right-4 duration-500">
          <Card className="border-zinc-200">
            <CardHeader className="flex flex-row items-center justify-between border-b border-zinc-50 pb-4">
              <div>
                <CardTitle className="font-serif text-xl flex items-center gap-2">
                  <Gift className="text-amber-600" size={20} /> Exclusive Offers
                </CardTitle>
                <CardDescription>Coupons and discounts curated for your Style DNA</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {offers.length === 0 ? (
                  <div className="col-span-full py-12 text-center text-zinc-400 bg-zinc-50/50 rounded-xl border border-dashed border-zinc-200">
                    <Tag className="mx-auto h-10 w-10 mb-3 opacity-30" />
                    <p>No active offers right now. Keep shopping to unlock rewards!</p>
                  </div>
                ) : (
                  offers.map((offer) => (
                    <div key={offer.offer_id} className="flex bg-white rounded-2xl border border-zinc-200 overflow-hidden shadow-sm hover:shadow-md transition-all group">
                      <div className="bg-gradient-to-br from-amber-500 to-amber-600 text-white p-5 flex flex-col justify-center items-center font-bold w-[120px] border-r border-dashed border-white/40">
                        <span className="text-3xl">{offer.discount_value}{offer.discount_type === 'percentage' ? '%' : '₹'}</span>
                        <span className="text-[10px] font-medium uppercase tracking-widest opacity-90 mt-1">OFF</span>
                      </div>
                      <div className="p-5 flex-1 flex flex-col justify-center">
                        <h4 className="font-bold text-zinc-900 mb-1">{offer.offer_name}</h4>
                        <p className="text-xs text-zinc-500 mb-3 leading-relaxed">{offer.condition_text}</p>
                        <div className="mt-auto flex items-center justify-between">
                          <span className="text-[10px] uppercase font-bold tracking-wider text-amber-600 bg-amber-50 px-2 py-1 rounded-md">
                            Valid till {new Date(offer.expires_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
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
                    {/* Explicit Form Mapping for Card Schema */}
                    <div className="space-y-2">
                      <Label>Cardholder Name</Label>
                      <Input value={newCard.card_name} onChange={e => setNewCard({...newCard, card_name: e.target.value})} placeholder="Full name on card" />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Card Brand</Label>
                        <Select value={newCard.card_brand} onValueChange={(val) => setNewCard({...newCard, card_brand: val})}>
                          <SelectTrigger><SelectValue placeholder="Select Brand" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="visa">Visa</SelectItem>
                            <SelectItem value="mastercard">Mastercard</SelectItem>
                            <SelectItem value="rupay">RuPay</SelectItem>
                            <SelectItem value="amex">Amex</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Last 4 Digits</Label>
                        <Input 
                          value={newCard.card_last4} 
                          onChange={e => setNewCard({...newCard, card_last4: e.target.value.replace(/\D/g, '').slice(0, 4)})} 
                          placeholder="e.g. 1234" 
                          maxLength={4} 
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Secure Token</Label>
                      <Input value={newCard.token} onChange={e => setNewCard({...newCard, token: e.target.value})} placeholder="e.g. tok_test_123" />
                      <p className="text-[10px] text-zinc-500">Provide the mock payment gateway token for testing.</p>
                    </div>

                    <div className="flex items-center gap-2 pt-2">
                      <input 
                        type="checkbox" 
                        id="is_default_card" 
                        checked={newCard.is_default} 
                        onChange={e => setNewCard({...newCard, is_default: e.target.checked})} 
                        className="rounded border-zinc-300 accent-black w-4 h-4" 
                      />
                      <Label htmlFor="is_default_card" className="font-normal cursor-pointer">Set as default payment method</Label>
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
                        <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 font-bold">
                          {card.card_brand} Secure
                        </p>
                        <button onClick={() => handleRemoveCard(card.id)} className="text-zinc-600 hover:text-red-400 transition-colors bg-white/5 p-1.5 rounded-full backdrop-blur-sm relative z-10">
                          <Trash2 size={12} />
                        </button>
                      </div>
                      
                      <p className="font-mono text-xl text-white mb-6 tracking-wider relative z-10">
                        •••• •••• •••• {card.card_last4}
                      </p>
                      
                      <div className="flex justify-between items-end text-xs font-medium relative z-10">
                        <div>
                          <p className="text-zinc-600 text-[9px] uppercase mb-0.5">Card Holder</p>
                          <span className="uppercase text-zinc-200">{card.card_name}</span>
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
          className="text-red-600 hover:text-red-700 hover:bg-red-50 gap-2 px-6 rounded-full"
        >
          <LogOut size={16} /> Sign Out
        </Button>
      </div>
    </div>
  );
}