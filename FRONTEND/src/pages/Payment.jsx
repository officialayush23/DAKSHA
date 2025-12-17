//     FRONTEND/src/pages/Payment.jsx

import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient";
import api from "@/lib/apiClient";
import { toast } from "sonner";
import {
  CreditCard,
  Wallet,
  ArrowLeft,
  ShieldCheck,
  Lock,
  Loader2,
  MapPin,
  Check,
  Truck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function PaymentPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Data passed from Cart page (DISPLAY ONLY)
  const { addressId, summary, items } = location.state || {};

  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [savedCards, setSavedCards] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState("cod");
  const [selectedAddress, setSelectedAddress] = useState(null);

  // --------------------------------------------------
  // SAFETY CHECK
  // --------------------------------------------------
  useEffect(() => {
    if (!addressId || !items || items.length === 0) {
      toast.error("Checkout session expired");
      navigate("/cart");
    }
  }, [addressId, items, navigate]);

  // --------------------------------------------------
  // LOAD ADDRESS + PAYMENT METHODS
  // --------------------------------------------------
  useEffect(() => {
    const loadData = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();

        if (!user) return;

        if (addressId) {
          const { data: addr } = await supabase
            .from("user_addresses")
            .select("*")
            .eq("id", addressId)
            .single();

          setSelectedAddress(addr);
        }

        const { data: cards } = await supabase
          .from("user_payment_methods")
          .select("*")
          .eq("user_id", user.id)
          .order("is_default", { ascending: false });

        setSavedCards(cards || []);
        if (cards?.length) setPaymentMethod(cards[0].id);
      } catch (err) {
        console.error("Payment load failed", err);
        toast.error("Failed to load payment info");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [addressId]);

  // --------------------------------------------------
  // CHECKOUT — SINGLE SOURCE OF TRUTH
  // --------------------------------------------------
  const handlePlaceOrder = async () => {
    setProcessing(true);
    try {
      const res = await api.post("/commerce/checkout", {
        order_type: "delivery",
        delivery_address_id: addressId,
        pickup_location_id: null,
        promotion_code: summary?.promoCode || null,
        payment_method: {
          type: paymentMethod === "cod" ? "cod" : "card",
          payment_method_id:
            paymentMethod === "cod" ? null : paymentMethod,
        },
      });

      toast.success("Order confirmed");
      navigate("/orders");
    } catch (err) {
      console.error("Checkout failed", err);
      toast.error(
        err?.response?.data?.detail ||
          "Checkout failed. A support agent has been notified."
      );
    } finally {
      setProcessing(false);
    }
  };

  // --------------------------------------------------
  // LOADING STATE
  // --------------------------------------------------
  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // --------------------------------------------------
  // UI
  // --------------------------------------------------
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* HEADER */}
      <div className="border-b border-border/40 bg-background/60 backdrop-blur sticky top-0 z-30">
        <div className="container max-w-6xl mx-auto h-16 flex items-center justify-between px-4">
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-foreground -ml-2"
            onClick={() => navigate("/cart")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" /> Cancel Checkout
          </Button>

          <div className="flex items-center gap-2 text-sm font-medium text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full">
            <Lock className="h-3.5 w-3.5" /> Secure Session
          </div>
        </div>
      </div>

      <div className="container max-w-6xl mx-auto py-10 px-4">
        <div className="grid lg:grid-cols-12 gap-8">
          {/* LEFT */}
          <div className="lg:col-span-8 space-y-8">
            {/* ADDRESS */}
            <section>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-primary" /> Shipping Address
              </h2>

              <Card className="bg-card/95 border border-border/60">
                <CardContent className="p-6 flex items-start justify-between">
                  {selectedAddress ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">
                          {selectedAddress.type}
                        </Badge>
                        {selectedAddress.is_default && (
                          <span className="text-xs text-muted-foreground">
                            Default
                          </span>
                        )}
                      </div>
                      <p className="font-medium text-lg pt-1">
                        {selectedAddress.address_line}
                      </p>
                      <p className="text-muted-foreground">
                        {selectedAddress.city} -{" "}
                        {selectedAddress.pincode}
                      </p>
                    </div>
                  ) : (
                    <Skeleton className="h-16 w-full" />
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate("/cart")}
                  >
                    Change
                  </Button>
                </CardContent>
              </Card>
            </section>

            {/* PAYMENT METHODS */}
            <section>
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" /> Payment Method
              </h2>

              <div className="grid gap-4">
                {savedCards.map((card) => (
                  <div
                    key={card.id}
                    onClick={() => setPaymentMethod(card.id)}
                    className={`cursor-pointer border rounded-xl transition-all ${
                      paymentMethod === card.id
                        ? "border-primary ring-1 ring-primary"
                        : "border-border/60 hover:border-border"
                    }`}
                  >
                    <div className="p-6 flex items-center justify-between bg-card">
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-10 rounded-md bg-zinc-800 flex items-center justify-center text-white">
                          <CreditCard className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="font-medium">
                            •••• •••• •••• {card.card_last4}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {card.card_brand?.toUpperCase()}
                          </p>
                        </div>
                      </div>

                      {paymentMethod === card.id && (
                        <Check className="h-5 w-5 text-primary" />
                      )}
                    </div>
                  </div>
                ))}

                {/* COD */}
                <div
                  onClick={() => setPaymentMethod("cod")}
                  className={`cursor-pointer border rounded-xl transition-all ${
                    paymentMethod === "cod"
                      ? "border-emerald-500 bg-emerald-500/5"
                      : "border-border/60 hover:border-border"
                  }`}
                >
                  <div className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-10 rounded-md bg-emerald-100 flex items-center justify-center">
                        <Truck className="h-5 w-5 text-emerald-700" />
                      </div>
                      <div>
                        <p className="font-medium">Cash on Delivery</p>
                        <p className="text-xs text-muted-foreground">
                          Pay at doorstep
                        </p>
                      </div>
                    </div>

                    {paymentMethod === "cod" && (
                      <Check className="h-5 w-5 text-emerald-500" />
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* RIGHT */}
          <div className="lg:col-span-4">
            <div className="sticky top-24">
              <Card className="bg-card/95 border border-border/60 shadow-xl">
                <CardHeader>
                  <CardTitle>Order Summary</CardTitle>
                  <CardDescription>
                    Review before payment
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  {items?.slice(0, 3).map((item, idx) => (
                    <div
                      key={idx}
                      className="flex justify-between text-sm"
                    >
                      <span className="text-muted-foreground">
                        {item.quantity}x {item.product_name}
                      </span>
                      <span>
                        ₹{(item.price * item.quantity).toFixed(0)}
                      </span>
                    </div>
                  ))}

                  <Separator />

                  <div className="flex justify-between font-bold text-lg">
                    <span>Total</span>
                    <span>₹{summary?.total?.toFixed(2)}</span>
                  </div>
                </CardContent>

                <CardFooter className="flex-col gap-4">
                  <Button
                    className="w-full h-12 text-base font-semibold"
                    onClick={handlePlaceOrder}
                    disabled={processing}
                  >
                    {processing ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin mr-2" />
                        Processing…
                      </>
                    ) : (
                      `Pay ₹${summary?.total?.toFixed(0)}`
                    )}
                  </Button>

                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <ShieldCheck className="h-3 w-3" /> SSL secured
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
