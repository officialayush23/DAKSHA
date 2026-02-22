import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import { KioskService } from '@/lib/kioskApi';
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Loader2, Store, Monitor } from 'lucide-react';
import { toast } from 'sonner';

export default function KioskSelectScreen() {
  const navigate = useNavigate();
  const { setKioskId } = useKiosk();

  const [stores, setStores] = useState([]);
  const [kiosks, setKiosks] = useState([]);
  const [selectedStore, setSelectedStore] = useState(null);
  const [loadingStores, setLoadingStores] = useState(true);
  const [loadingKiosks, setLoadingKiosks] = useState(false);

  useEffect(() => {
    const fetchStores = async () => {
      try {
        const data = await KioskService.listStores();
        setStores(data || []);
      } catch (error) {
        toast.error("Could not load stores");
      } finally {
        setLoadingStores(false);
      }
    };
    fetchStores();
  }, []);

  const handleStoreSelect = async (store) => {
    setSelectedStore(store);
    setLoadingKiosks(true);
    try {
      const data = await KioskService.listKiosksForStore(store.id);
      setKiosks(data || []);
    } catch (error) {
      toast.error("Could not load kiosks");
    } finally {
      setLoadingKiosks(false);
    }
  };

  const handleKioskSelect = (kiosk) => {
    setKioskId(kiosk.id);
    toast.success(`Kiosk "${kiosk.name}" selected`);
    navigate('/kiosk/login');
  };

  return (
    <div className="h-screen w-full bg-slate-50 flex flex-col items-center justify-center p-12 gap-10">
      
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-5xl font-bold text-slate-900">Setup Kiosk</h1>
        <p className="text-xl text-slate-500">Select your store and kiosk to continue</p>
      </div>

      <div className="w-full max-w-4xl grid grid-cols-2 gap-8">

        {/* Left: Stores */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-slate-700 flex items-center gap-2">
            <Store className="w-6 h-6" /> Select Store
          </h2>
          {loadingStores ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-10 h-10 animate-spin text-slate-300" />
            </div>
          ) : (
            <div className="space-y-3">
              {stores.map(store => (
                <Card
                  key={store.id}
                  onClick={() => handleStoreSelect(store)}
                  className={`p-5 cursor-pointer transition-all border-2 hover:border-primary ${
                    selectedStore?.id === store.id
                      ? 'border-primary bg-primary/5'
                      : 'border-slate-200'
                  }`}
                >
                  <p className="text-xl font-bold text-slate-900">{store.name}</p>
                  <p className="text-slate-500">{store.city}, {store.state}</p>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Right: Kiosks */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-slate-700 flex items-center gap-2">
            <Monitor className="w-6 h-6" /> Select Kiosk
          </h2>
          {!selectedStore ? (
            <div className="flex justify-center py-12 text-slate-400 text-lg">
              Select a store first
            </div>
          ) : loadingKiosks ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-10 h-10 animate-spin text-slate-300" />
            </div>
          ) : kiosks.length === 0 ? (
            <div className="flex justify-center py-12 text-slate-400 text-lg">
              No active kiosks found
            </div>
          ) : (
            <div className="space-y-3">
              {kiosks.map(kiosk => (
                <Card
                  key={kiosk.id}
                  onClick={() => handleKioskSelect(kiosk)}
                  className="p-5 cursor-pointer transition-all border-2 border-slate-200 hover:border-green-500 hover:bg-green-50"
                >
                  <p className="text-xl font-bold text-slate-900">{kiosk.name}</p>
                  <p className="text-slate-500 text-sm">{kiosk.id}</p>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}