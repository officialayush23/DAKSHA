// src/pages/ProfilePage.jsx
import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { UserService } from '../lib/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, Button } from 'antd';
import { MapPin, CreditCard, Star } from 'lucide-react';
import { toast } from 'sonner';

export default function ProfilePage() {
  const queryClient = useQueryClient();

  // Fetching data using the updated API wrappers
  const { data: profile } = useQuery({ 
    queryKey: ['profile'], 
    queryFn: () => UserService.getProfile().then(r => r.data) 
  });
  
  const { data: loyalty } = useQuery({ 
    queryKey: ['loyalty'], 
    queryFn: () => UserService.getLoyalty().then(r => r.data) 
  });
  
  const { data: addresses } = useQuery({ 
    queryKey: ['addresses'], 
    queryFn: () => UserService.getAddresses().then(r => r.data) 
  });

  return (
    <div className="max-w-5xl mx-auto space-y-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-end pb-8 border-b border-gray-100">
        <div>
          <h1 className="text-5xl md:text-6xl font-serif mb-2 tracking-tight">My Atelier</h1>
          <p className="text-gray-400 uppercase tracking-widest text-xs font-medium">Member since 2026</p>
        </div>
        <div className="mt-6 md:mt-0 bg-black text-white px-8 py-4 rounded-full flex items-center gap-3 shadow-xl shadow-black/10">
          <Star className="fill-white" size={18} />
          <span className="font-bold text-sm tracking-wide">{loyalty?.points || 0} Points</span>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="mb-10 bg-gray-50 p-1 rounded-full w-fit border border-gray-100">
          <TabsTrigger value="overview" className="rounded-full px-8 py-2 data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-black text-gray-500 font-medium text-sm transition-all">Overview</TabsTrigger>
          <TabsTrigger value="orders" className="rounded-full px-8 py-2 data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-black text-gray-500 font-medium text-sm transition-all">Orders</TabsTrigger>
          <TabsTrigger value="settings" className="rounded-full px-8 py-2 data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-black text-gray-500 font-medium text-sm transition-all">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-12 animate-in fade-in slide-in-from-bottom-4">
          
          {/* Addresses */}
          <section>
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-serif text-2xl tracking-tight">Saved Addresses</h3>
              <Button type="dashed" shape="round" className="border-gray-300 text-gray-500 hover:text-black hover:border-black" onClick={() => toast("Open Address Modal")}>
                + Add New
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {addresses?.map(addr => (
                <Card key={addr.id} hoverable className="border-gray-100 shadow-sm rounded-2xl">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-gray-50 rounded-full">
                        <MapPin className="text-black" size={18} />
                    </div>
                    <div>
                      <p className="font-bold text-sm uppercase mb-1 tracking-wide">{addr.label}</p>
                      <p className="text-gray-500 text-sm leading-relaxed">
                        {addr.address_line1}<br/>
                        {addr.city}, {addr.state} - {addr.pincode}
                      </p>
                      {addr.is_default && <span className="text-[10px] bg-black text-white px-2 py-0.5 rounded-md mt-3 inline-block uppercase tracking-wider">Default</span>}
                    </div>
                  </div>
                </Card>
              ))}
              {(!addresses || addresses.length === 0) && (
                <div className="col-span-full py-16 text-center text-gray-400 border border-dashed border-gray-200 rounded-2xl bg-gray-50/50">
                  <p className="text-sm">No addresses saved yet.</p>
                </div>
              )}
            </div>
          </section>

          {/* Wallet */}
          <section>
            <h3 className="font-serif text-2xl mb-6 tracking-tight">Wallet & Cards</h3>
            <div className="p-8 bg-gradient-to-br from-zinc-900 to-black text-white rounded-3xl w-full md:w-96 shadow-2xl ring-1 ring-white/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
              <div className="relative z-10">
                <div className="flex justify-between items-start mb-12">
                    <CreditCard size={32} className="opacity-80" />
                    <span className="font-serif italic text-xl tracking-tight">Daksha Priority</span>
                </div>
                <p className="font-mono text-xl tracking-[0.2em] mb-6 opacity-90">•••• •••• •••• 4242</p>
                <div className="flex justify-between text-[10px] uppercase tracking-[0.2em] opacity-60 font-medium">
                    <span>{profile?.name || 'CARD HOLDER'}</span>
                    <span>EXP 12/28</span>
                </div>
              </div>
            </div>
          </section>

        </TabsContent>

        <TabsContent value="orders">
           <div className="py-32 text-center text-gray-400 font-serif text-xl border border-dashed border-gray-200 rounded-3xl bg-gray-50/30">
             Your order history will appear here.
           </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}