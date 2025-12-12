import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient";
import { toast } from "sonner";
import { 
  CreditCard, Wallet, ArrowLeft, ShieldCheck, 
  Lock, Loader2, MapPin, Check, Truck
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";

export default function PaymentPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Data from Cart Page
  const { addressId, summary, items } = location.state || {};

  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [savedCards, setSavedCards] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState("cod"); 
  const [selectedAddress, setSelectedAddress] = useState(null);

  // --- Redirect Logic ---
  useEffect(() => {
    if (!addressId || !items || items.length === 0) {
      // toast.error("Session expired.");
      // navigate("/cart");
    }
  }, [addressId, items, navigate]);

  // --- 1. Fetch Data ---
  useEffect(() => {
    const loadData = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        // Fetch Address
        if (addressId) {
          const { data: addr } = await supabase
            .from('user_addresses')
            .select('*')
            .eq('id', addressId)
            .single();
          setSelectedAddress(addr);
        }

        // Fetch Cards
        const { data: cards } = await supabase
          .from('user_payment_methods')
          .select('*')
          .eq('user_id', user.id)
          .order('is_default', { ascending: false });
        
        setSavedCards(cards || []);
        
        // Auto-select
        if (cards?.length > 0) setPaymentMethod(cards[0].id);

      } catch (err) {
        console.error("Load error", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [addressId]);

  // --- 2. Transaction Logic ---
  const handlePlaceOrder = async () => {
    setProcessing(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("Not logged in");

      // A. Create Order
      const { data: order, error: orderError } = await supabase
        .from('orders')
        .insert({
          user_id: user.id,
          status: 'pending',
          type: 'delivery',
          total_amount: summary?.total || 0,
          delivery_address_id: addressId,
        })
        .select()
        .single();

      if (orderError) throw orderError;

      // B. Create Order Items
      const orderItemsData = items.map(item => ({
        order_id: order.id,
        product_variant_id: item.product_variant_id || item.id,
        quantity: item.quantity,
        price_at_purchase: item.price
      }));

      const { error: itemsError } = await supabase.from('order_items').insert(orderItemsData);
      if (itemsError) throw itemsError;

      // C. Create Payment Record
      const { error: payError } = await supabase.from('payments').insert({
        order_id: order.id,
        user_id: user.id,
        amount: summary?.total || 0,
        provider: paymentMethod === 'cod' ? 'cash' : 'card',
        status: 'success' 
      });

      if (payError) throw payError;

      // D. Clear Cart
      const { data: cart } = await supabase.from('carts').select('id').eq('user_id', user.id).eq('status', 'active').maybeSingle();
      if (cart) {
        await supabase.from('cart_items').delete().eq('cart_id', cart.id);
      }

      toast.success("Order confirmed!");
      navigate("/orders");

    } catch (err) {
      console.error(err);
      toast.error("Transaction failed.");
    } finally {
      setProcessing(false);
    }
  };

  if (loading) return <div className="h-screen w-full flex items-center justify-center bg-background"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>;

  return (
    <div className="min-h-screen bg-background text-foreground">
      
      {/* --- Minimal Header --- */}
      <div className="border-b border-border/40 bg-background/50 backdrop-blur sticky top-0 z-30">
        <div className="container max-w-6xl mx-auto h-16 flex items-center justify-between px-4">
          <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground -ml-2" onClick={() => navigate("/cart")}>
            <ArrowLeft className="h-4 w-4 mr-2" /> Cancel Checkout
          </Button>
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full">
            <Lock className="h-3.5 w-3.5" /> Secure Session
          </div>
        </div>
      </div>

      <div className="container max-w-6xl mx-auto py-10 px-4">
        <div className="grid lg:grid-cols-12 gap-8">
          
          {/* --- LEFT COLUMN (Payment Selection) --- */}
          <div className="lg:col-span-8 space-y-8">
            
            {/* 1. Shipping Address Summary */}
            <section>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-primary" /> Shipping Address
              </h2>
              <Card className="bg-card border-border/50">
                <CardContent className="p-6 flex items-start justify-between">
                  {selectedAddress ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="capitalize">{selectedAddress.type}</Badge>
                        {selectedAddress.is_default && <span className="text-xs text-muted-foreground">Default</span>}
                      </div>
                      <p className="font-medium text-lg pt-1">{selectedAddress.address_line}</p>
                      <p className="text-muted-foreground">{selectedAddress.city} - {selectedAddress.pincode}</p>
                    </div>
                  ) : (
                    <Skeleton className="h-16 w-full" />
                  )}
                  <Button variant="outline" size="sm" onClick={() => navigate("/cart")}>Change</Button>
                </CardContent>
              </Card>
            </section>

            {/* 2. Payment Methods */}
            <section>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" /> Payment Method
              </h2>
              
              <div className="grid gap-4">
                
                {/* A. Saved Cards */}
                {savedCards.map((card) => (
                  <div 
                    key={card.id}
                    onClick={() => setPaymentMethod(card.id)}
                    className={`relative overflow-hidden group cursor-pointer border rounded-xl transition-all duration-300 ${paymentMethod === card.id ? 'border-primary ring-1 ring-primary' : 'border-border/50 hover:border-border'}`}
                  >
                    <div className="p-6 flex items-center justify-between bg-card">
                      <div className="flex items-center gap-4">
                        {/* Visual Card Icon */}
                        <div className={`w-14 h-10 rounded-md bg-gradient-to-br flex items-center justify-center text-white shadow-sm ${card.card_brand === 'visa' ? 'from-blue-600 to-blue-800' : 'from-orange-500 to-red-600'}`}>
                           <span className="font-bold text-[10px] uppercase">{card.card_brand?.slice(0,4)}</span>
                        </div>
                        <div>
                          <p className="font-medium text-base">•••• •••• •••• {card.card_last4}</p>
                          <p className="text-xs text-muted-foreground">Expires 12/28</p>
                        </div>
                      </div>
                      
                      {/* Check Circle */}
                      <div className={`h-6 w-6 rounded-full border flex items-center justify-center transition-colors ${paymentMethod === card.id ? 'bg-primary border-primary text-primary-foreground' : 'border-muted-foreground/30'}`}>
                        {paymentMethod === card.id && <Check className="h-3.5 w-3.5" />}
                      </div>
                    </div>
                  </div>
                ))}

                {/* B. Cash on Delivery */}
                <div 
                  onClick={() => setPaymentMethod('cod')}
                  className={`cursor-pointer border rounded-xl transition-all duration-300 ${paymentMethod === 'cod' ? 'border-emerald-500 bg-emerald-500/5 ring-1 ring-emerald-500' : 'border-border/50 hover:border-border bg-card'}`}
                >
                  <div className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-10 rounded-md bg-emerald-100 flex items-center justify-center text-emerald-700">
                         <Truck className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-medium text-base">Cash on Delivery</p>
                        <p className="text-xs text-muted-foreground">Pay safely when your order arrives.</p>
                      </div>
                    </div>
                    
                    <div className={`h-6 w-6 rounded-full border flex items-center justify-center transition-colors ${paymentMethod === 'cod' ? 'bg-emerald-500 border-emerald-500 text-white' : 'border-muted-foreground/30'}`}>
                      {paymentMethod === 'cod' && <Check className="h-3.5 w-3.5" />}
                    </div>
                  </div>
                </div>

              </div>
            </section>
          </div>

          {/* --- RIGHT COLUMN (Sticky Summary) --- */}
          <div className="lg:col-span-4">
            <div className="sticky top-24">
              <Card className="border-border/50 bg-card shadow-lg">
                <CardHeader className="bg-muted/20 border-b border-border/50 pb-4">
                  <CardTitle className="text-lg">Order Summary</CardTitle>
                  <CardDescription>Review costs before paying</CardDescription>
                </CardHeader>
                <CardContent className="pt-6 space-y-4">
                  
                  {/* Items Preview */}
                  <div className="space-y-3">
                    {items?.slice(0, 3).map((item, idx) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span className="text-muted-foreground line-clamp-1 flex-1 pr-2">{item.quantity}x {item.product_name}</span>
                        <span>₹{(item.price * item.quantity).toFixed(0)}</span>
                      </div>
                    ))}
                    {items?.length > 3 && <p className="text-xs text-muted-foreground pt-1">...and {items.length - 3} more items</p>}
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Subtotal</span>
                      <span>₹{summary?.subtotal?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Shipping</span>
                      <span className="text-emerald-500 font-medium">{summary?.shipping === 0 ? "Free" : `₹${summary?.shipping}`}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Taxes</span>
                      <span>₹{summary?.tax?.toFixed(2)}</span>
                    </div>
                  </div>

                  <Separator />

                  <div className="flex justify-between items-center py-2">
                    <span className="font-bold text-lg">Total</span>
                    <span className="font-bold text-2xl">₹{summary?.total?.toFixed(2)}</span>
                  </div>
                </CardContent>

                <CardFooter className="p-6 bg-muted/20 border-t border-border/50 flex-col gap-4">
                  <Button 
                    className="w-full h-12 text-base font-semibold shadow-lg bg-primary hover:bg-primary/90" 
                    onClick={handlePlaceOrder}
                    disabled={processing}
                  >
                    {processing ? (
                      <><Loader2 className="h-5 w-5 animate-spin mr-2" /> Processing...</>
                    ) : (
                      `Pay ₹${summary?.total?.toFixed(0)}`
                    )}
                  </Button>
                  <div className="flex items-center justify-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                    <ShieldCheck className="h-3 w-3" /> SSL Encrypted Transaction
                  </div>
                </CardFooter>
              </Card>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}