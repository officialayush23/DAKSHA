import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  CartService, CheckoutService, SessionService, 
  UserService, LoyaltyService, ProductService 
} from '../lib/api';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";

import { 
  Truck, Store, MapPin, Navigation, CheckCircle2, 
  ChevronRight, Loader2, Tag, CreditCard, ShoppingBag, Award, List
} from 'lucide-react';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  // --- CORE DATA ---
  const [step, setStep] = useState(1);
  const [cart, setCart] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [checkoutId, setCheckoutId] = useState(null);
  const [lockedPrice, setLockedPrice] = useState(0);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [loyaltySummary, setLoyaltySummary] = useState(null);

  // --- FULFILLMENT ---
  const [fulfillmentType, setFulfillmentType] = useState('delivery');
  
  // Delivery State
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState("");

  // Pickup State
  const [stores, setStores] = useState([]);
  const [selectedStoreId, setSelectedStoreId] = useState("");
  const [locating, setLocating] = useState(false);
  const [manualLat, setManualLat] = useState("");
  const [manualLng, setManualLng] = useState("");

  // --- PAYMENT & CARDS ---
  const [cards, setCards] = useState([]);
  const [selectedCardId, setSelectedCardId] = useState("");

  // --- OFFERS ---
  const [coupons, setCoupons] = useState([]); 
  const [couponCode, setCouponCode] = useState("");
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [discountAmount, setDiscountAmount] = useState(0);
  const [useLoyalty, setUseLoyalty] = useState(false);

  // ==========================================
  // 1. SMART LOAD DATA (ENRICHMENT)
  // ==========================================
  useEffect(() => {
    const bootstrap = async () => {
      try {
        const [cartRes, sessRes, addrRes, loyaltyRes, cardsRes] = await Promise.all([
          CartService.get().catch(() => null),
          SessionService.getActive().catch(() => null),
          UserService.getAddresses().catch(() => ({ data: [] })),
          LoyaltyService.getSummary().catch(() => null),
          UserService.getCards().catch(() => ({ data: [] }))
        ]);
        
        let cartData = cartRes?.data || cartRes || { items: [] };
        if (!cartData.items || cartData.items.length === 0) {
          toast.error("Your cart is empty.");
          navigate('/dash/shop');
          return;
        }

        const uniqueProductIds = [...new Set(cartData.items.map(i => i.product_id).filter(Boolean))];
        const productResponses = await Promise.all(
          uniqueProductIds.map(id => ProductService.getDetail(id).catch(() => null))
        );
        
        const variantLookup = {};
        productResponses.forEach(prod => {
          const p = prod?.data || prod;
          if (!p || !p.variants) return;
          p.variants.forEach(v => {
            variantLookup[v.variant_id] = {
              name: p.name,
              brand: p.brand,
              final_price: v.final_price || v.base_price,
              base_price: v.base_price,
              discount_percent: v.discount_percent || 0,
              image: v.images?.[0] || v.image_url || v.image || p.image
            };
          });
        });

        let enrichedSubtotal = 0;
        cartData.items = cartData.items.map(item => {
          const liveData = variantLookup[item.variant_id] || {};
          const finalPrice = liveData.final_price || item.base_price || 0;
          const basePrice = liveData.base_price || item.base_price || 0;
          const discount = liveData.discount_percent || 0;
          const itemTotal = finalPrice * item.quantity;
          
          enrichedSubtotal += itemTotal;

          return {
            ...item,
            live_name: liveData.name || "Premium Item",
            live_brand: liveData.brand || "Daksha",
            live_final_price: finalPrice,
            live_base_price: basePrice,
            live_discount: discount,
            live_item_total: itemTotal,
            live_image: liveData.image || item.image_url || "https://placehold.co/400x500/F8F9FA/a1a1aa?text=No+Image"
          };
        });

        cartData.grand_total = enrichedSubtotal;
        setCart(cartData);
        setSessionId(sessRes?.data?.session_id || sessRes?.session_id);
        setLoyaltySummary(loyaltyRes?.data || loyaltyRes);
        
        const userAddresses = Array.isArray(addrRes?.data) ? addrRes.data : (Array.isArray(addrRes) ? addrRes : []);
        setAddresses(userAddresses);
        if (userAddresses.length > 0) setSelectedAddressId(userAddresses[0].id);

        const userCards = Array.isArray(cardsRes?.data) ? cardsRes.data : (Array.isArray(cardsRes) ? cardsRes : []);
        setCards(userCards);
        const defaultCard = userCards.find(c => c.is_default) || userCards[0];
        if (defaultCard) setSelectedCardId(defaultCard.id);

      } catch (error) {
        toast.error("Failed to load checkout data.");
        navigate('/dash/cart');
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, [navigate]);

  // ==========================================
  // 2. FETCH PICKUP STORES
  // ==========================================
  const fetchStoresFromAPI = async (lat, lng) => {
    try {
      const cartId = cart.cart_id || cart.id;
      const res = await CheckoutService.getPickupStores(cartId, lat, lng);
      const storeList = Array.isArray(res?.data) ? res.data : (Array.isArray(res) ? res : []);
      
      setStores(storeList);
      if (storeList.length > 0) {
        // 👇 FIXED: Backend returns store_id, not id
        setSelectedStoreId(storeList[0].store_id || storeList[0].id);
        toast.success(`Found ${storeList.length} stores`);
      } else {
        toast.info("No stores found in this area.");
      }
    } catch (err) {
      toast.error("Backend issue retrieving stores.");
      setStores([]); 
    } finally {
      setLocating(false);
    }
  };

  const handleAutoLocate = () => {
    if (!("geolocation" in navigator)) return toast.error("Geolocation not supported");

    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(4);
        const lng = position.coords.longitude.toFixed(4);
        
        setManualLat(lat);
        setManualLng(lng);
        
        toast.success("Location detected!");
        fetchStoresFromAPI(parseFloat(lat), parseFloat(lng));
      },
      (error) => {
        toast.error("Please allow location access to find stores.");
        setLocating(false);
      },
      { timeout: 10000 }
    );
  };

  const handleManualStoreSearch = (e) => {
    e.preventDefault();
    if (!manualLat || !manualLng) return toast.error("Please enter both latitude and longitude");
    setLocating(true);
    fetchStoresFromAPI(parseFloat(manualLat), parseFloat(manualLng));
  };

  const handleListAllStores = () => {
    setLocating(true);
    toast.info("Fetching available boutiques...");
    fetchStoresFromAPI(18.0, 73.0); 
  };

  // ==========================================
  // 3. START CHECKOUT
  // ==========================================
  const handleStartCheckout = async () => {
    if (fulfillmentType === 'delivery' && !selectedAddressId) return toast.error("Please select a delivery address.");
    if (fulfillmentType === 'pickup' && !selectedStoreId) return toast.error("Please select a pickup store.");

    setProcessing(true);
    try {
      const payload = {
        user_id: user?.id,
        session_id: sessionId,
        cart_id: cart.cart_id || cart.id,
      };

      let res;
      if (fulfillmentType === 'delivery') {
        res = await CheckoutService.startDelivery(payload);
      } else {
        res = await CheckoutService.startPickup({ ...payload, store_id: selectedStoreId });
      }

      const resData = res?.data || res;
      const cId = resData?.checkout_id;
      if (!cId) throw new Error("Invalid checkout session generated");
      
      setCheckoutId(cId);
      setLockedPrice(resData?.locked_price || cart.grand_total);

      const couponRes = await CheckoutService.getCoupons(cId).catch(() => ({ data: { personalized: [], system: [] } }));
      const cData = couponRes?.data || couponRes;
      
      const availableCoupons = [...(cData?.system || []), ...(cData?.personalized || [])];
      setCoupons(availableCoupons);

      setStep(2);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to initialize secure checkout.");
    } finally {
      setProcessing(false);
    }
  };

  // ==========================================
  // 4. COUPONS & FINALIZE ORDER
  // ==========================================
  const executeApplyCoupon = async (code_or_id) => {
    setProcessing(true);
    try {
      const matchingCoupon = coupons.find(c => c.code === code_or_id || c.id === code_or_id);
      
      let payload = { coupon_code: null, offer_id: null };

      if (matchingCoupon) {
        if (matchingCoupon.personalized) {
          payload.offer_id = matchingCoupon.id; 
        } else {
          payload.coupon_code = matchingCoupon.code;
        }
      } else {
        payload.coupon_code = code_or_id;
      }

      const res = await CheckoutService.applyCoupon(checkoutId, payload);
      const resData = res?.data || res;
      
      toast.success("Coupon applied successfully!");
      
      const displayCode = matchingCoupon?.code || matchingCoupon?.offer_name || code_or_id;
      setAppliedCoupon({ code: displayCode });
      setCouponCode(displayCode);
      setDiscountAmount(resData.discount_amount || 0);

    } catch (error) {
      toast.error(error?.response?.data?.detail || "Invalid or expired coupon");
    } finally {
      setProcessing(false);
    }
  };

  const handleApplyCouponForm = (e) => {
    e?.preventDefault();
    if (!couponCode) return;
    executeApplyCoupon(couponCode);
  };

  const handleFinalizeOrder = async () => {
    if (!selectedCardId) return toast.error("Please select a payment method");
    
    setProcessing(true);
    try {
      let scheduledTime = null;
      if (fulfillmentType === 'pickup') {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1); 
        scheduledTime = tomorrow.toISOString();
      }

      const payload = {
        delivery_address_id: fulfillmentType === 'delivery' ? selectedAddressId : null,
        scheduled_time: scheduledTime, 
        redeem_loyalty_points: useLoyalty ? (loyaltySummary?.points || 0) : 0
      };

      const res = await CheckoutService.finalizeOrder(checkoutId, payload);
      const resData = res?.data || res;

      if (resData.status === "already_completed") {
        toast.info("This order has already been processed.");
      } else {
        toast.success("Order confirmed successfully! 🎉");
      }
      navigate('/dash/orders');
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Failed to finalize order.");
    } finally {
      setProcessing(false);
    }
  };

  // ==========================================
  // RENDER UI
  // ==========================================
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-10 animate-pulse grid md:grid-cols-12 gap-10">
        <Skeleton className="md:col-span-8 h-[600px] rounded-[2rem]" />
        <Skeleton className="md:col-span-4 h-[400px] rounded-[2rem]" />
      </div>
    );
  }

  const subtotal = step === 2 ? lockedPrice : (cart?.grand_total || 0);
  const deliveryFee = 0; 
  const loyaltyDiscount = useLoyalty && loyaltySummary ? (loyaltySummary.points * 0.5) : 0; 
  const finalTotal = Math.max(0, subtotal + deliveryFee - discountAmount - loyaltyDiscount);

  return (
    <div className="min-h-screen bg-[#FDFDFD] pb-24">
      <div className="bg-white border-b border-zinc-100 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
          <h1 className="font-serif text-2xl font-bold tracking-tight text-zinc-900">Checkout</h1>
          <div className="flex items-center gap-3 text-xs font-bold uppercase tracking-widest text-zinc-300">
            <span className={step >= 1 ? "text-zinc-900" : ""}>1. Details</span>
            <ChevronRight size={14} />
            <span className={step >= 2 ? "text-zinc-900" : ""}>2. Payment</span>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 md:px-6 pt-10 grid grid-cols-1 md:grid-cols-12 gap-10 lg:gap-16">
        
        {/* LEFT COLUMN */}
        <div className="md:col-span-7 lg:col-span-8 space-y-8">
          <AnimatePresence mode="wait">
            
            {/* STEP 1 */}
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-10">
                
                {/* Method Selection */}
                <div>
                  <h2 className="text-xl font-serif font-bold mb-4 text-zinc-900">How would you like to receive this?</h2>
                  <div className="grid grid-cols-2 gap-4">
                    <button onClick={() => setFulfillmentType('delivery')} className={`p-6 rounded-[1.5rem] border-2 flex flex-col items-center justify-center gap-3 transition-all duration-300 ${fulfillmentType === 'delivery' ? 'border-zinc-900 bg-zinc-50 shadow-sm' : 'border-zinc-100 bg-white hover:border-zinc-200'}`}>
                      <Truck size={24} className={fulfillmentType === 'delivery' ? 'text-zinc-900' : 'text-zinc-400'} />
                      <span className={`text-sm font-bold tracking-wide ${fulfillmentType === 'delivery' ? 'text-zinc-900' : 'text-zinc-500'}`}>Ship to Address</span>
                    </button>
                    <button onClick={() => setFulfillmentType('pickup')} className={`p-6 rounded-[1.5rem] border-2 flex flex-col items-center justify-center gap-3 transition-all duration-300 ${fulfillmentType === 'pickup' ? 'border-zinc-900 bg-zinc-50 shadow-sm' : 'border-zinc-100 bg-white hover:border-zinc-200'}`}>
                      <Store size={24} className={fulfillmentType === 'pickup' ? 'text-zinc-900' : 'text-zinc-400'} />
                      <span className={`text-sm font-bold tracking-wide ${fulfillmentType === 'pickup' ? 'text-zinc-900' : 'text-zinc-500'}`}>Pick up in Store</span>
                    </button>
                  </div>
                </div>

                <Separator className="bg-zinc-100" />

                {/* DELIVERY FLOW */}
                {fulfillmentType === 'delivery' && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-serif font-bold text-zinc-900">Shipping Address</h2>
                      <Button variant="ghost" className="text-xs font-bold uppercase tracking-widest text-zinc-500 hover:text-black">Add New</Button>
                    </div>
                    {addresses.length === 0 ? (
                      <div className="p-8 border border-zinc-200 border-dashed rounded-[1.5rem] text-center bg-zinc-50/50">
                        <MapPin size={24} className="mx-auto text-zinc-300 mb-2" />
                        <p className="text-zinc-500 text-sm font-medium">Please add an address in your profile to continue.</p>
                      </div>
                    ) : (
                      <div className="grid gap-3">
                        {addresses.map(addr => (
                          <div key={addr.id} onClick={() => setSelectedAddressId(addr.id)} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${selectedAddressId === addr.id ? 'border-zinc-900 bg-zinc-50 shadow-sm' : 'border-zinc-100 bg-white hover:border-zinc-200'}`}>
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-bold text-zinc-900">{addr.label || 'Home'}</h4>
                                <p className="text-sm text-zinc-500 mt-1">{addr.address_line1} {addr.address_line2}</p>
                                <p className="text-sm text-zinc-500">{addr.city}, {addr.state} {addr.pincode}</p>
                              </div>
                              {selectedAddressId === addr.id && <CheckCircle2 className="text-black" size={20} />}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}

                {/* PICKUP FLOW ENHANCED */}
                {fulfillmentType === 'pickup' && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-6">
                    
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <h2 className="text-xl font-serif font-bold text-zinc-900">Find a Store</h2>
                      <Button 
                        onClick={handleAutoLocate} 
                        disabled={locating} 
                        variant="outline" 
                        className="rounded-full text-xs font-bold tracking-widest uppercase border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:text-blue-800"
                      >
                        {locating ? <Loader2 className="animate-spin mr-2 h-3 w-3" /> : <Navigation className="mr-2 h-3 w-3" />} 
                        Auto-Locate Me
                      </Button>
                    </div>

                    <form onSubmit={handleManualStoreSearch} className="flex flex-col sm:flex-row gap-3">
                      <div className="flex-1">
                        <Input 
                          placeholder="Latitude (e.g. 18.52)" 
                          value={manualLat} 
                          onChange={(e) => setManualLat(e.target.value)} 
                          className="h-12 rounded-xl bg-zinc-50 border-zinc-200 focus-visible:ring-black" 
                          type="number" step="any" 
                        />
                      </div>
                      <div className="flex-1">
                        <Input 
                          placeholder="Longitude (e.g. 73.85)" 
                          value={manualLng} 
                          onChange={(e) => setManualLng(e.target.value)} 
                          className="h-12 rounded-xl bg-zinc-50 border-zinc-200 focus-visible:ring-black" 
                          type="number" step="any" 
                        />
                      </div>
                      <Button type="submit" disabled={locating} className="h-12 rounded-xl bg-zinc-900 text-white px-8 font-bold uppercase tracking-widest text-xs">
                        {locating ? <Loader2 className="animate-spin" /> : 'Search'}
                      </Button>
                    </form>

                    {stores.length === 0 ? (
                      <div className="p-10 border border-zinc-200 bg-zinc-50 rounded-[1.5rem] text-center">
                        <Store size={32} className="mx-auto text-zinc-300 mb-3" />
                        <p className="text-zinc-600 font-medium text-sm mb-4">Click Auto-Locate or enter coordinates to find nearby boutiques.</p>
                        
                        <Button 
                          onClick={handleListAllStores}
                          variant="ghost" 
                          className="text-xs font-bold uppercase tracking-widest text-zinc-500 hover:text-black"
                        >
                          <List size={14} className="mr-2" /> Show All Available Stores
                        </Button>
                      </div>
                    ) : (
                      <div className="grid gap-3">
                        {stores.map(store => {
                          // 👇 FIXED: Correct keys
                          const currentStoreId = store.store_id || store.id;
                          return (
                          <div key={currentStoreId} onClick={() => setSelectedStoreId(currentStoreId)} className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${selectedStoreId === currentStoreId ? 'border-zinc-900 bg-zinc-50 shadow-sm' : 'border-zinc-100 bg-white hover:border-zinc-200'}`}>
                            <div className="flex justify-between items-start">
                              <div>
                                <h4 className="font-bold text-zinc-900 flex items-center gap-2">{store.name} <Badge variant="secondary" className="text-[9px] uppercase shadow-none bg-emerald-100 text-emerald-700">In Stock</Badge></h4>
                                <p className="text-sm text-zinc-500 mt-1">{store.address}</p>
                                {/* 👇 FIXED: distance_km from swagger */}
                                {store.distance_km && <p className="text-xs font-bold text-zinc-400 mt-2">{parseFloat(store.distance_km).toFixed(1)} km away</p>}
                              </div>
                              {selectedStoreId === currentStoreId && <CheckCircle2 className="text-black" size={20} />}
                            </div>
                          </div>
                        )})}
                      </div>
                    )}
                  </motion.div>
                )}

                <Button 
                  onClick={handleStartCheckout} 
                  disabled={processing || (fulfillmentType === 'delivery' ? !selectedAddressId : !selectedStoreId)}
                  className="w-full h-14 rounded-full bg-zinc-900 hover:bg-black text-white font-bold tracking-[0.15em] uppercase text-sm shadow-xl active:scale-95 transition-all disabled:opacity-50"
                >
                  {processing ? <Loader2 className="animate-spin mr-2" /> : null} Proceed to Payment
                </Button>
              </motion.div>
            )}

            {/* STEP 2: FINALIZE */}
            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="space-y-8">
                
                <div className="flex items-center justify-between p-5 bg-zinc-50 rounded-[1.5rem] border border-zinc-100">
                  <div className="flex items-center gap-4">
                    <div className="bg-white p-3 rounded-xl border border-zinc-200 shadow-sm">
                      {fulfillmentType === 'delivery' ? <Truck size={20} className="text-zinc-900" /> : <Store size={20} className="text-zinc-900" />}
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Fulfillment</p>
                      <p className="font-bold text-sm text-zinc-900">{fulfillmentType === 'delivery' ? 'Standard Delivery' : 'Store Pickup'}</p>
                    </div>
                  </div>
                  <Button variant="link" onClick={() => setStep(1)} className="text-xs font-bold underline text-zinc-500 hover:text-black">Change</Button>
                </div>

                {/* SAVED CARDS UI */}
                <div>
                  <h2 className="text-xl font-serif font-bold mb-4 text-zinc-900">Select Payment Method</h2>
                  {cards.length === 0 ? (
                    <div className="p-8 border border-zinc-200 border-dashed rounded-[1.5rem] text-center bg-zinc-50/50">
                      <CreditCard size={24} className="mx-auto text-zinc-300 mb-2" />
                      <p className="text-zinc-500 text-sm font-medium">No saved cards found in your profile.</p>
                    </div>
                  ) : (
                    <div className="grid gap-3">
                      {cards.map(card => (
                        <div 
                          key={card.id} 
                          onClick={() => setSelectedCardId(card.id)}
                          className={`p-5 rounded-2xl border-2 cursor-pointer transition-all ${selectedCardId === card.id ? 'border-zinc-900 bg-zinc-50 shadow-sm' : 'border-zinc-100 bg-white hover:border-zinc-200'}`}
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-4">
                              <div className="p-2 bg-white rounded-lg border border-zinc-200 shadow-sm">
                                <CreditCard size={24} className={selectedCardId === card.id ? "text-zinc-900" : "text-zinc-400"} />
                              </div>
                              <div>
                                <p className="font-bold text-zinc-900 uppercase">
                                  {card.card_brand} <span className="text-zinc-500 font-medium lowercase tracking-wide mr-1">ending in</span> {card.card_last4}
                                </p>
                                <p className="text-xs text-zinc-500 mt-0.5">{card.card_name}</p>
                              </div>
                            </div>
                            {selectedCardId === card.id && <CheckCircle2 className="text-black" size={20} />}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <Button 
                  onClick={handleFinalizeOrder} 
                  disabled={processing || !selectedCardId}
                  className="w-full h-14 rounded-full bg-black hover:bg-zinc-800 text-white font-bold tracking-[0.15em] uppercase text-sm shadow-xl active:scale-95 transition-all disabled:opacity-50"
                >
                  {processing ? <Loader2 className="animate-spin mr-2" /> : <ShoppingBag className="mr-2 h-4 w-4" />}
                  Pay ₹{finalTotal} & Place Order
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* RIGHT COLUMN */}
        <div className="md:col-span-5 lg:col-span-4">
          <Card className="rounded-[2rem] border-zinc-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] sticky top-28 bg-white">
            <CardContent className="p-6 md:p-8 space-y-6">
              <h3 className="font-serif font-bold text-xl text-zinc-900">Order Summary</h3>
              
              <div className="space-y-4 max-h-[300px] overflow-y-auto scrollbar-hide pr-2">
                {cart?.items?.map((item) => (
                  // 👇 FIXED: Secure unique key
                  <div key={item.product_variant_id || item.variant_id} className="flex gap-4 items-center">
                    <div className="w-16 h-20 bg-[#F8F9FA] rounded-xl overflow-hidden shrink-0 border border-zinc-100 flex items-center justify-center p-1 relative">
                      {item.live_discount > 0 && (
                        <Badge className="absolute top-1 left-1 z-10 bg-red-500 text-white text-[8px] font-bold px-1.5 py-0.5 shadow-sm border-none">
                          -{item.live_discount}%
                        </Badge>
                      )}
                      <img src={item.live_image} alt={item.live_name} className="w-full h-full object-contain mix-blend-multiply" />
                    </div>
                    <div className="flex-1 flex flex-col justify-center">
                      <h4 className="text-[10px] uppercase tracking-widest text-zinc-400 font-bold mb-0.5">{item.live_brand}</h4>
                      <h4 className="text-sm font-bold text-zinc-900 line-clamp-1">{item.live_name}</h4>
                      <p className="text-xs text-zinc-500 mt-0.5">Qty: {item.quantity}</p>
                      
                      <div className="flex items-center gap-2 mt-1">
                        <p className="text-sm font-bold text-black">₹{item.live_item_total}</p>
                        {item.live_discount > 0 && (
                          <p className="text-[10px] text-zinc-400 line-through">₹{item.live_base_price * item.quantity}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <Separator className="bg-zinc-100" />

              {/* Coupons Block */}
              <div className={`space-y-4 transition-opacity ${step === 1 ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">Promotions</p>
                <form onSubmit={handleApplyCouponForm} className="flex gap-2">
                  <Input 
                    value={couponCode} onChange={(e) => setCouponCode(e.target.value)}
                    placeholder="Enter code" 
                    className="h-12 rounded-xl border-zinc-200 bg-zinc-50 text-sm focus-visible:ring-1 focus-visible:ring-black uppercase font-medium tracking-wide" 
                  />
                  <Button type="submit" disabled={!couponCode || processing} variant="outline" className="h-12 rounded-xl px-5 font-bold text-xs uppercase tracking-widest">Apply</Button>
                </form>
                
                {coupons.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {coupons.map(c => {
                      const id_or_code = c.code || c.id;
                      const displayName = c.code || c.offer_name || "OFFER";
                      return (
                        <Badge 
                          key={id_or_code} 
                          variant="secondary" 
                          onClick={() => executeApplyCoupon(id_or_code)} 
                          className="cursor-pointer bg-zinc-100 hover:bg-zinc-200 text-zinc-700 shadow-none font-bold uppercase tracking-widest text-[9px] py-1.5 px-3 transition-colors"
                        >
                          <Tag size={10} className="mr-1" /> {displayName}
                        </Badge>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Loyalty Points */}
              {loyaltySummary?.points > 0 && (
                <div className={`pt-2 transition-opacity ${step === 1 ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
                  <div className="flex items-center justify-between p-4 rounded-xl border border-amber-100 bg-amber-50/50">
                    <div className="flex items-center gap-3">
                      <Award className="text-amber-500" size={20} />
                      <div>
                        <p className="text-xs font-bold text-amber-900 uppercase tracking-widest">Daksha Rewards</p>
                        <p className="text-xs font-medium text-amber-700/80 mt-0.5">Use {loyaltySummary.points} pts for -₹{loyaltySummary.points * 0.5}</p>
                      </div>
                    </div>
                    <Switch checked={useLoyalty} onCheckedChange={setUseLoyalty} />
                  </div>
                </div>
              )}

              <Separator className="bg-zinc-100" />

              {/* Math Totals */}
              <div className="space-y-3 text-sm font-medium text-zinc-500">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span className="text-zinc-900 font-bold">₹{subtotal}</span>
                </div>
                <div className="flex justify-between">
                  <span>Shipping</span>
                  <span className="text-emerald-600 font-bold tracking-widest uppercase text-xs mt-0.5">
                    FREE
                  </span>
                </div>
                {appliedCoupon && (
                  <div className="flex justify-between text-emerald-600">
                    <span>Discount ({appliedCoupon.code})</span>
                    <span className="font-bold">-₹{discountAmount}</span>
                  </div>
                )}
                {useLoyalty && (
                  <div className="flex justify-between text-amber-600">
                    <span>Loyalty Points</span>
                    <span className="font-bold">-₹{loyaltyDiscount}</span>
                  </div>
                )}
              </div>

              <Separator className="bg-zinc-900" />

              <div className="flex justify-between items-end pt-2">
                <span className="text-xs font-bold uppercase tracking-widest text-zinc-400 mb-1">Total To Pay</span>
                <span className="text-3xl font-serif font-bold text-black">₹{finalTotal}</span>
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}