import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { UserService, LoyaltyService } from '../lib/api';
import { Button } from "@/components/ui/button";
import { Send, User, MapPin, LogOut, Award } from 'lucide-react';
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

export default function ProfilePage() {
  const { user, signOut } = useAuth();
  const [profile, setProfile] = useState(null);
  const [points, setPoints] = useState(0);

  useEffect(() => {
    UserService.getProfile().then(res => setProfile(res));
    LoyaltyService.getPoints().then(res => setPoints(res.points));
  }, []);

  const handleTelegramLink = () => {
    // Construct Deep Link: https://t.me/YourBot?start={user_id}
    const botUsername = "Daksha_Retail_Bot"; // Replace with your real bot name
    const url = `https://t.me/${botUsername}?start=${user.id}`;
    window.open(url, '_blank');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-6 p-8 bg-black text-white rounded-3xl">
        <Avatar className="h-24 w-24 border-4 border-white/20">
          <AvatarFallback className="bg-zinc-800 text-3xl font-serif">
            {user?.email?.[0].toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div>
          <h1 className="text-3xl font-serif font-bold">{profile?.name || "Member"}</h1>
          <p className="text-zinc-400">{user?.email}</p>
          <div className="flex gap-2 mt-4">
            <Badge className="bg-amber-400 text-black hover:bg-amber-500 flex gap-1 items-center">
              <Award size={12} /> {points} Points
            </Badge>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Telegram Connect */}
        <div className="bg-[#24A1DE]/10 p-6 rounded-3xl border border-[#24A1DE]/20">
          <div className="flex items-center gap-3 mb-4 text-[#24A1DE]">
            <Send size={24} />
            <h3 className="font-bold text-lg">Connect Telegram</h3>
          </div>
          <p className="text-sm text-zinc-600 mb-6">
            Get instant order updates, delivery notifications, and chat with our concierge directly on Telegram.
          </p>
          <Button onClick={handleTelegramLink} className="w-full bg-[#24A1DE] hover:bg-[#2090C5] text-white rounded-full">
            Start Bot
          </Button>
        </div>

        {/* Addresses */}
        <div className="bg-white p-6 rounded-3xl border border-zinc-100">
          <div className="flex items-center gap-3 mb-4 text-zinc-900">
            <MapPin size={24} />
            <h3 className="font-bold text-lg">Addresses</h3>
          </div>
          <p className="text-sm text-zinc-500 mb-4">Manage your shipping locations.</p>
          <Button variant="outline" className="w-full rounded-full">Manage</Button>
        </div>
      </div>
      
      <div className="text-center pt-8">
        <Button variant="ghost" className="text-red-500" onClick={signOut}>
          <LogOut className="mr-2 h-4 w-4" /> Sign Out
        </Button>
      </div>
    </div>
  );
}