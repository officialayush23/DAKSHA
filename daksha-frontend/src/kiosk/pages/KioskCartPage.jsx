import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  ShoppingBag, ArrowRight, ArrowLeft,
  Trash2, Loader2, Sparkles, Tag,
} from 'lucide-react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';

export default function KioskCartPage() {
  const navigate = useNavigate();
  const { refreshCart, resetIdleTimer } = useKiosk();

  const [cart,       setCart]       = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [removing,   setRemoving]   = useState(null);
  const [couponCode, setCouponCode] = useState('');
  const [couponData, setCouponData] = useState(null);
  const [applyingCoupon, setApplyingCoupon] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get('/cart');
      setCart(res.data || res);
    } catch {
      toast.error('Could not load cart');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleRemove = async (variantId) => {
    setRemoving(variantId);
    resetIdleTimer();
    try {
      await api.delete(`/cart/item/${variantId}`);
      await load();
      await refreshCart();
      toast.success('Item removed');
    } catch {
      toast.error('Failed to remove item');
    } finally {
      setRemoving(null);
    }
  };

  const applyCoupon = async () => {
    if (!couponCode.trim()) return;
    setApplyingCoupon(true);
    resetIdleTimer();
    try {
      const res = await api.post('/cart/coupon', { code: couponCode.trim().toUpperCase() });
      setCouponData(res.data || res);
      toast.success('Coupon applied!');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Invalid coupon');
      setCouponData(null);
    } finally {
      setApplyingCoupon(false);
    }
  };

  const items  = cart?.items || [];
  const subtotal = items.reduce((acc, i) => acc + (i.price * i.quantity), 0);
  const discount = couponData?.discount_amount || 0;
  const total    = Math.max(0, subtotal - discount);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-white">
        <Loader2 className="w-16 h-16 animate-spin text-slate-300" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-80px)] flex flex-col bg-slate-50">

      {/* ── Header bar ─── */}
      <div className="bg-white border-b px-8 py-5 flex items-center gap-4 shadow-sm shrink-0">
        <button type="button" onClick={() => navigate(-1)}
          className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center hover:bg-slate-200 transition-colors">
          <ArrowLeft className="h-6 w-6 text-slate-700" />
        </button>
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <ShoppingBag className="w-8 h-8" /> Your Cart
          {items.length > 0 && (
            <Badge className="text-lg px-3 py-1 rounded-full">{items.length}</Badge>
          )}
        </h1>
      </div>

      {/* ── Body ─── */}
      {items.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-6 text-slate-400">
          <ShoppingBag className="w-28 h-28 opacity-20" />
          <p className="text-3xl font-semibold">Your cart is empty</p>
          <div className="flex gap-4 mt-4">
            <Button type="button" size="lg" variant="outline" className="h-16 px-10 text-xl rounded-2xl"
              onClick={() => navigate('/kiosk/shop')}>
              Browse Catalog
            </Button>
            <Button type="button" size="lg" className="h-16 px-10 text-xl rounded-2xl bg-slate-900 gap-3"
              onClick={() => navigate('/kiosk/chat')}>
              <Sparkles className="w-6 h-6" /> Ask Daksha AI
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex gap-0 overflow-hidden">

          {/* Left: Items list */}
          <div className="flex-1 overflow-y-auto p-8 space-y-5">
            <AnimatePresence>
              {items.map((item) => (
                <motion.div
                  key={item.product_variant_id || item.id}
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="bg-white rounded-3xl p-6 flex items-center gap-6 shadow-sm"
                >
                  {/* Thumbnail */}
                  <div
                    className="w-28 h-28 rounded-2xl overflow-hidden bg-slate-100 shrink-0 cursor-pointer"
                    onClick={() => item.product_id && navigate(`/kiosk/product/${item.product_id}`)}
                  >
                    <img
                      src={item.image || 'https://via.placeholder.com/112'}
                      alt={item.product_name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0 space-y-1">
                    <p className="text-xl font-bold text-slate-900 truncate">{item.product_name}</p>
                    {(item.color || item.size) && (
                      <p className="text-base text-slate-400">{[item.color, item.size].filter(Boolean).join(' · ')}</p>
                    )}
                    <p className="text-2xl font-bold text-slate-900">
                      ₹{(item.price * item.quantity).toLocaleString('en-IN')}
                      <span className="text-base font-normal text-slate-400 ml-2">× {item.quantity}</span>
                    </p>
                  </div>

                  {/* Remove */}
                  <button
                    type="button"
                    onClick={() => handleRemove(item.product_variant_id)}
                    disabled={removing === item.product_variant_id}
                    className="h-14 w-14 rounded-2xl bg-red-50 text-red-400 hover:bg-red-100 hover:text-red-600 transition-colors flex items-center justify-center shrink-0"
                  >
                    {removing === item.product_variant_id
                      ? <Loader2 className="h-6 w-6 animate-spin" />
                      : <Trash2 className="h-6 w-6" />}
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Continue shopping */}
            <Button type="button" variant="ghost" size="lg" className="text-slate-400 text-lg gap-2"
              onClick={() => navigate('/kiosk/shop')}>
              <ArrowLeft className="w-5 h-5" /> Continue Shopping
            </Button>
          </div>

          {/* Right: Summary panel */}
          <div className="w-[380px] bg-white border-l p-8 flex flex-col gap-6 shrink-0 overflow-y-auto">

            <h2 className="text-2xl font-bold text-slate-900">Order Summary</h2>

            {/* Price breakdown */}
            <div className="space-y-3 text-lg">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal ({items.length} items)</span>
                <span>₹{subtotal.toLocaleString('en-IN')}</span>
              </div>
              {discount > 0 && (
                <div className="flex justify-between text-green-600 font-medium">
                  <span>Coupon Discount</span>
                  <span>− ₹{discount.toLocaleString('en-IN')}</span>
                </div>
              )}
              <Separator />
              <div className="flex justify-between text-2xl font-bold text-slate-900">
                <span>Total</span>
                <span>₹{total.toLocaleString('en-IN')}</span>
              </div>
            </div>

            {/* Coupon input */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                <Tag className="w-4 h-4" /> Coupon Code
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={couponCode}
                  onChange={(e) => { resetIdleTimer(); setCouponCode(e.target.value.toUpperCase()); }}
                  placeholder="Enter code"
                  className="flex-1 h-14 px-4 rounded-xl border-2 border-slate-200 text-lg font-mono uppercase focus:border-slate-900 outline-none transition-colors"
                />
                <Button
                  type="button"
                  size="lg"
                  variant="outline"
                  disabled={applyingCoupon || !couponCode.trim()}
                  onClick={applyCoupon}
                  className="h-14 px-5 rounded-xl text-lg"
                >
                  {applyingCoupon ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Apply'}
                </Button>
              </div>
              {couponData && (
                <p className="text-green-600 text-sm font-medium">
                  ✓ {couponData.message || `₹${discount} off applied`}
                </p>
              )}
            </div>

            {/* Checkout CTA */}
            <div className="mt-auto space-y-3">
              <Button
                type="button"
                size="lg"
                className="w-full h-20 text-2xl rounded-2xl bg-slate-900 hover:bg-slate-700 gap-3 font-semibold shadow-xl"
                onClick={() => { resetIdleTimer(); navigate('/kiosk/checkout'); }}
              >
                Checkout <ArrowRight className="w-7 h-7" />
              </Button>

              <Button
                type="button"
                variant="ghost"
                size="lg"
                className="w-full h-14 text-lg text-slate-500 gap-2 rounded-2xl"
                onClick={() => navigate('/kiosk/chat')}
              >
                <Sparkles className="w-5 h-5" /> Ask Daksha AI for help
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
