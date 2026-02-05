import React, { useState, useEffect } from 'react';
import { CheckoutService } from '../lib/api';
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, MapPin, Truck, Store } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('init');
  const [pickupOptions, setPickupOptions] = useState([]);
  const [deliveryType, setDeliveryType] = useState('delivery'); // 'delivery' | 'pickup'

  useEffect(() => {
    // Fetch pickup stores if user wants pickup
    if (deliveryType === 'pickup' && "geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(async (pos) => {
        try {
          const res = await CheckoutService.getPickupOptions(pos.coords.latitude, pos.coords.longitude);
          setPickupOptions(res.data || []);
        } catch (e) {
          console.error(e);
        }
      });
    }
  }, [deliveryType]);

  const handleCheckout = async () => {
    setLoading(true);
    setStatus('processing');
    
    try {
      const { checkout_id } = await CheckoutService.start();
      
      // Simulate Payment
      await new Promise(resolve => setTimeout(resolve, 2000));
      const key = `idempotency-${Date.now()}`;
      await CheckoutService.pay(checkout_id, key);
      
      setStatus('success');
      toast.success("Order Placed!");
      setTimeout(() => navigate('/dash/orders'), 3000);
      
    } catch (error) {
      setStatus('failed');
      toast.error("Checkout Failed");
    } finally {
      setLoading(false);
    }
  };

  if (status === 'success') {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6 animate-bounce">
          <CheckCircle size={40} />
        </div>
        <h1 className="text-4xl font-serif font-bold mb-4">Order Confirmed</h1>
        <p className="text-zinc-500 mb-8">Thank you for your purchase.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-12">
      <h1 className="text-3xl font-serif font-bold mb-8">Checkout</h1>
      
      <div className="bg-white p-8 rounded-3xl border border-zinc-100 shadow-xl space-y-8">
        
        {/* Step 1: Delivery Method */}
        <div>
          <h3 className="font-bold text-lg mb-4 flex items-center gap-2"><Truck size={20} /> Fulfillment</h3>
          <div className="grid grid-cols-2 gap-4">
            <div 
              onClick={() => setDeliveryType('delivery')}
              className={`border-2 p-4 rounded-xl cursor-pointer ${deliveryType === 'delivery' ? 'border-black bg-zinc-50' : 'border-zinc-200'}`}
            >
              <span className="font-bold block">Delivery</span>
              <span className="text-sm text-zinc-500">To your address</span>
            </div>
            <div 
              onClick={() => setDeliveryType('pickup')}
              className={`border-2 p-4 rounded-xl cursor-pointer ${deliveryType === 'pickup' ? 'border-black bg-zinc-50' : 'border-zinc-200'}`}
            >
              <span className="font-bold block">Pickup</span>
              <span className="text-sm text-zinc-500">From nearest store</span>
            </div>
          </div>
        </div>

        {/* Step 2: Details */}
        {deliveryType === 'pickup' && (
          <div>
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2"><Store size={20} /> Select Store</h3>
            {pickupOptions.length > 0 ? (
              <div className="space-y-2">
                {pickupOptions.map(store => (
                  <div key={store.store_id} className="p-3 border rounded-lg hover:bg-zinc-50 cursor-pointer">
                    <div className="font-bold">{store.name}</div>
                    <div className="text-xs text-zinc-500">{store.city} ({store.distance_km} km away)</div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-zinc-400">Locating stores...</p>}
          </div>
        )}

        <Button onClick={handleCheckout} disabled={loading} className="w-full h-16 text-lg rounded-full">
          {loading ? <Loader2 className="animate-spin mr-2" /> : null}
          {status === 'processing' ? 'Processing...' : 'Place Order'}
        </Button>
      </div>
    </div>
  );
}