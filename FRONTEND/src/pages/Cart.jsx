// FRONTEND/src/pages/Cart.jsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/apiClient";
import {supabase} from "@/lib/supabaseClient";
import { toast } from "sonner";
import { 
  ShoppingBag, Trash2, Plus, Minus, ArrowRight, MapPin, 
  ShieldCheck, Loader2, ArrowLeft, Store, AlertTriangle
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function CartPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [cartItems, setCartItems] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [orderSummary, setOrderSummary] = useState({ subtotal: 0, tax: 0, total: 0 });
  const [debugMsg, setDebugMsg] = useState(null); // For troubleshooting

  // --- 1. Robust Fetch Logic ---
  const fetchCart = async () => {
    try {
      setLoading(true);
      if (!user) return;

      // A. Fetch Addresses
      const { data: addrData } = await supabase
        .from('user_addresses')
        .select('*')
        .eq('user_id', user.id)
        .order('is_default', { ascending: false });
      
      setAddresses(addrData || []);
      if (addrData?.length > 0) setSelectedAddressId(addrData[0].id);

      // B. Fetch Active Cart ID
      const { data: cartData, error: cartError } = await supabase
        .from('carts')
        .select('id')
        .eq('user_id', user.id)
        .eq('status', 'active')
        .maybeSingle(); // Use maybeSingle to avoid 406 errors if 0 rows

      if (cartError) {
        console.error("Error finding cart:", cartError);
        return;
      }

      if (!cartData) {
        setCartItems([]);
        return;
      }

      // C. Fetch Items with Join
      const { data: items, error: itemsError } = await supabase
        .from('cart_items')
        .select(`
          id,
          quantity,
          product_variant_id,
          product_variants (
            id,
            price_override,
            size_label,
            color_name,
            image_url,
            products (
              name,
              base_price
            )
          )
        `)
        .eq('cart_id', cartData.id)
        .order('id', { ascending: true });

      if (itemsError) {
        console.error("Error fetching items:", itemsError);
        setDebugMsg("Could not load items. Check RLS policies.");
        return;
      }

      // D. Transform Data (Handle missing relations gracefully)
      const formatted = items.map(item => {
        const variant = item.product_variants || {};
        const product = variant.products || {};
        
        // Fallback pricing logic
        const price = variant.price_override || product.base_price || 0;

        return {
          id: item.id,
          product_name: product.name || "Item Loaded (No Details)",
          variant_name: variant.color_name ? `${variant.color_name} / ${variant.size_label}` : "Standard",
          price: Number(price),
          quantity: item.quantity,
          image_url: variant.image_url
        };
      });

      setCartItems(formatted);

    } catch (err) {
      console.error("Cart crash:", err);
      toast.error("Failed to load cart.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) fetchCart();
  }, [user]);

  // --- 2. Calculations ---
  useEffect(() => {
    const subtotal = cartItems.reduce((acc, item) => acc + (item.price * item.quantity), 0);
    const tax = subtotal * 0.05; 
    const shipping = subtotal > 1000 ? 0 : 50; 
    setOrderSummary({ subtotal, tax, shipping, total: subtotal + tax + shipping });
  }, [cartItems]);

  // --- 3. Handlers ---
  const handleRemoveItem = async (itemId) => {
    // Optimistic
    const prev = [...cartItems];
    setCartItems(curr => curr.filter(i => i.id !== itemId));

    const { error } = await supabase.from('cart_items').delete().eq('id', itemId);
    if (error) {
      setCartItems(prev);
      toast.error("Failed to delete");
    } else {
      toast.success("Item removed");
    }
  };

  const handleUpdateQty = async (itemId, newQty) => {
    if (newQty < 1) return;
    
    // Optimistic
    setCartItems(curr => curr.map(i => i.id === itemId ? { ...i, quantity: newQty } : i));
    
    // DB
    await supabase.from('cart_items').update({ quantity: newQty }).eq('id', itemId);
  };

  const handleProceedToPay = () => {
    if (!selectedAddressId) return toast.error("Please select a delivery address.");
    if (cartItems.length === 0) return toast.error("Cart is empty.");
    navigate("/payment", { state: { addressId: selectedAddressId, summary: orderSummary, items: cartItems } });
  };

  if (loading) return <CartSkeleton />;

  if (cartItems.length === 0) {
    return (
      <div className="container max-w-4xl mx-auto py-24 px-4 flex flex-col items-center justify-center text-center space-y-6">
        <div className="bg-muted/50 p-8 rounded-full">
            <ShoppingBag className="h-16 w-16 text-muted-foreground/50" />
        </div>
        <div className="space-y-2">
            <h2 className="text-2xl font-bold">Your cart is empty</h2>
            <p className="text-muted-foreground max-w-sm mx-auto">
              {debugMsg ? <span className="text-red-500">{debugMsg}</span> : "Looks like you haven't added anything yet."}
            </p>
        </div>
        <Button onClick={() => navigate("/products")} size="lg" className="mt-4 gap-2">
          <ArrowLeft className="h-4 w-4" /> Start Shopping
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur sticky top-0 z-30">
        <div className="container max-w-6xl mx-auto h-16 flex items-center gap-4 px-4">
            <Button variant="ghost" size="sm" className="gap-2" onClick={() => navigate("/products")}>
                <ArrowLeft className="h-4 w-4" /> Back to Shopping
            </Button>
            <div className="h-6 w-[1px] bg-border mx-2 hidden sm:block"></div>
            <h1 className="text-lg font-semibold flex items-center gap-2">
                <ShoppingBag className="h-5 w-5" /> Your Cart
                <Badge variant="secondary" className="ml-2">{cartItems.length} Items</Badge>
            </h1>
        </div>
      </div>

      <div className="container max-w-6xl mx-auto py-8 px-4">
        <div className="grid lg:grid-cols-3 gap-8">
          
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            
            <Card>
              <CardHeader className="pb-4"><CardTitle>Cart Items</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                {cartItems.map((item) => (
                  <div key={item.id} className="flex gap-4 group">
                     {/* Image */}
                     <div className="h-28 w-24 bg-muted rounded-md flex items-center justify-center shrink-0 overflow-hidden border border-border/50">
                       {item.image_url ? (
                           <img src={item.image_url} className="h-full w-full object-cover" alt="product" />
                       ) : (
                           <ShoppingBag className="h-8 w-8 text-muted-foreground/30" />
                       )}
                     </div>
                     
                     {/* Details */}
                     <div className="flex-1 flex flex-col justify-between py-1">
                       <div>
                         <div className="flex justify-between items-start">
                             <h3 className="font-medium text-base line-clamp-2">{item.product_name}</h3>
                             <p className="font-bold text-lg">₹{(item.price * item.quantity).toFixed(0)}</p>
                         </div>
                         <p className="text-sm text-muted-foreground mt-1">{item.variant_name}</p>
                       </div>
                       
                       <div className="flex justify-between items-center mt-3">
                         <div className="flex items-center gap-1 border rounded-md bg-background shadow-sm">
                           <button className="h-8 w-8 flex items-center justify-center hover:bg-muted rounded-l-md" onClick={() => handleUpdateQty(item.id, item.quantity - 1)}><Minus className="h-3 w-3" /></button>
                           <span className="text-sm font-medium w-8 text-center">{item.quantity}</span>
                           <button className="h-8 w-8 flex items-center justify-center hover:bg-muted rounded-r-md" onClick={() => handleUpdateQty(item.id, item.quantity + 1)}><Plus className="h-3 w-3" /></button>
                         </div>
                         <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-destructive h-8 px-2" onClick={() => handleRemoveItem(item.id)}><Trash2 className="h-4 w-4 mr-2" /> Remove</Button>
                       </div>
                     </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-4">
                <CardTitle className="flex items-center gap-2"><MapPin className="h-5 w-5 text-muted-foreground" /> Delivery Address</CardTitle>
                <Button variant="link" onClick={() => navigate("/profile")} className="text-primary h-auto p-0">Add New +</Button>
              </CardHeader>
              <CardContent>
                {addresses.length === 0 ? (
                    <div className="text-center py-6 border-2 border-dashed rounded-lg bg-muted/20">
                        <p className="text-muted-foreground mb-3">No addresses found.</p>
                        <Button variant="outline" size="sm" onClick={() => navigate("/profile")}>Manage Addresses</Button>
                    </div>
                ) : (
                  <RadioGroup value={selectedAddressId} onValueChange={setSelectedAddressId} className="grid gap-3">
                    {addresses.map((addr) => (
                      <div key={addr.id} className={`relative flex items-start space-x-3 border p-4 rounded-lg cursor-pointer transition-all hover:border-primary/50 ${selectedAddressId === addr.id ? 'border-primary bg-primary/5 shadow-sm' : 'bg-card'}`}>
                        <RadioGroupItem value={addr.id} id={addr.id} className="mt-1" />
                        <Label htmlFor={addr.id} className="flex-1 cursor-pointer font-normal">
                          <div className="flex items-center gap-2 mb-1">
                              <span className="font-semibold capitalize">{addr.type}</span>
                              {addr.is_default && <Badge variant="secondary" className="text-[10px] h-5">Default</Badge>}
                          </div>
                          <p className="text-sm text-foreground">{addr.address_line}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{addr.city}, {addr.pincode}</p>
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24 shadow-lg border-primary/20 bg-card">
              <CardHeader className="bg-muted/40 pb-4 border-b"><CardTitle>Order Summary</CardTitle></CardHeader>
              <CardContent className="space-y-4 pt-6">
                <div className="flex justify-between text-sm"><span className="text-muted-foreground">Subtotal</span><span>₹{orderSummary.subtotal.toFixed(2)}</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted-foreground">Tax (5%)</span><span>₹{orderSummary.tax.toFixed(2)}</span></div>
                <div className="flex justify-between text-sm"><span className="text-muted-foreground">Shipping</span><span className={orderSummary.shipping === 0 ? "text-emerald-600 font-medium" : ""}>{orderSummary.shipping === 0 ? "Free" : `₹${orderSummary.shipping}`}</span></div>
                <Separator className="my-2" />
                <div className="flex justify-between items-center"><span className="font-bold text-lg">Total</span><span className="font-bold text-2xl text-primary">₹{orderSummary.total.toFixed(2)}</span></div>
              </CardContent>
              <CardFooter className="flex-col gap-4 bg-muted/40 p-6 border-t">
                <Button className="w-full h-12 text-base shadow-md font-semibold" onClick={handleProceedToPay}>Proceed to Payment <ArrowRight className="ml-2 h-4 w-4" /></Button>
                <div className="flex items-center justify-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground font-medium"><ShieldCheck className="h-3 w-3" /> Secure SSL Checkout</div>
              </CardFooter>
            </Card>
          </div>

        </div>
      </div>
    </div>
  );
}

function CartSkeleton() {
  return (
    <div className="container max-w-6xl mx-auto py-8 px-4">
        <Skeleton className="h-12 w-48 mb-8" />
        <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6"><Skeleton className="h-64 w-full rounded-xl" /><Skeleton className="h-48 w-full rounded-xl" /></div>
            <Skeleton className="h-96 w-full rounded-xl" />
        </div>
    </div>
  );
}