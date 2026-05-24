import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import api from '@/lib/api';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, ShoppingBag, Loader2, Sparkles, Check } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';

export default function KioskProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refreshCart, resetIdleTimer } = useKiosk();

  const [product,         setProduct]         = useState(null);
  const [variants,        setVariants]         = useState([]);
  const [loading,         setLoading]          = useState(true);
  const [adding,          setAdding]           = useState(false);
  const [addedVariantId,  setAddedVariantId]   = useState(null);
  const [selectedColor,   setSelectedColor]    = useState(null);
  const [selectedSize,    setSelectedSize]     = useState(null);
  const [selectedVariant, setSelectedVariant]  = useState(null);
  const [activeImage,     setActiveImage]      = useState(0);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/products/${id}`);
        const data = res.data || res;
        setProduct(data);
        const vlist = data.variants || [];
        setVariants(vlist);
        const firstColor = vlist.find(v => v.color)?.color || null;
        setSelectedColor(firstColor);
      } catch {
        toast.error('Could not load product');
        navigate('/kiosk/shop');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, navigate]);

  // Derive available sizes from selected color
  const colors = [...new Set(variants.map(v => v.color).filter(Boolean))];
  const availableSizes = variants
    .filter(v => v.color === selectedColor)
    .map(v => v.size)
    .filter(Boolean);

  // Resolve selected variant
  useEffect(() => {
    if (selectedColor && selectedSize) {
      setSelectedVariant(
        variants.find(v => v.color === selectedColor && v.size === selectedSize) || null
      );
    } else {
      setSelectedVariant(null);
    }
  }, [selectedColor, selectedSize, variants]);

  // Active images for the selected color
  const images = variants
    .filter(v => v.color === selectedColor)
    .flatMap(v => v.images || [])
    .filter(Boolean)
    .filter((url, i, arr) => arr.indexOf(url) === i);

  const handleAddToCart = async () => {
    if (!selectedVariant) return;
    setAdding(true);
    resetIdleTimer();
    try {
      const variantId = selectedVariant.variant_id || selectedVariant.id;
      await api.post('/cart/quick-add', { variant_id: variantId, quantity: 1 });
      await refreshCart();
      setAddedVariantId(variantId);
      toast.success('Added to cart!', { position: 'top-center' });
      setTimeout(() => setAddedVariantId(null), 2000);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to add to cart');
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-white">
        <Loader2 className="w-16 h-16 animate-spin text-slate-300" />
      </div>
    );
  }
  if (!product) return null;

  const displayPrice = selectedVariant?.final_price || selectedVariant?.base_price
    || variants[0]?.final_price || variants[0]?.base_price || 0;
  const originalPrice = selectedVariant?.original_price || variants[0]?.original_price;
  const discountPct = selectedVariant?.discount_percent || variants[0]?.discount_percent || 0;

  return (
    <div className="flex h-[calc(100vh-80px)] bg-white overflow-hidden">

      {/* ── LEFT: Image panel ─── */}
      <div className="w-[55%] bg-slate-50 relative flex flex-col">
        {/* Back button */}
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="absolute top-6 left-6 z-10 h-14 w-14 rounded-full bg-white shadow-md flex items-center justify-center hover:bg-slate-100 transition-colors"
        >
          <ArrowLeft className="h-7 w-7 text-slate-700" />
        </button>

        {/* Main image */}
        <div className="flex-1 flex items-center justify-center p-12">
          <motion.img
            key={images[activeImage] || 'placeholder'}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            src={images[activeImage] || 'https://via.placeholder.com/600x800'}
            alt={product.name}
            className="max-h-full max-w-full object-contain drop-shadow-2xl"
          />
        </div>

        {/* Thumbnail strip */}
        {images.length > 1 && (
          <div className="flex gap-3 justify-center pb-6 px-6">
            {images.slice(0, 5).map((img, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setActiveImage(i)}
                className={`w-16 h-16 rounded-xl overflow-hidden border-2 transition-all ${
                  activeImage === i ? 'border-slate-900 scale-105' : 'border-transparent opacity-60'
                }`}
              >
                <img src={img} alt="" className="w-full h-full object-cover" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ── RIGHT: Details panel ─── */}
      <div className="w-[45%] flex flex-col border-l overflow-y-auto">
        <div className="flex-1 p-10 space-y-8">

          {/* Brand + name + price */}
          <div className="space-y-3">
            {product.brand && (
              <p className="text-sm font-bold tracking-widest text-slate-400 uppercase">{product.brand}</p>
            )}
            <h1 className="text-4xl font-bold text-slate-900 leading-tight">{product.name}</h1>
            <div className="flex items-baseline gap-3 pt-1">
              <span className="text-4xl font-bold text-slate-900">
                ₹{displayPrice.toLocaleString('en-IN')}
              </span>
              {discountPct > 0 && originalPrice && (
                <>
                  <span className="text-2xl text-slate-400 line-through">
                    ₹{originalPrice.toLocaleString('en-IN')}
                  </span>
                  <Badge className="bg-green-100 text-green-700 text-base px-3 py-1">
                    {discountPct}% off
                  </Badge>
                </>
              )}
            </div>
          </div>

          {/* Description */}
          {product.description && (
            <p className="text-lg text-slate-500 leading-relaxed">{product.description}</p>
          )}

          {/* Fabric / Occasion */}
          {(product.fabric_type || product.occasion) && (
            <div className="flex gap-3 flex-wrap">
              {product.fabric_type && (
                <Badge variant="outline" className="text-base px-3 py-1">{product.fabric_type}</Badge>
              )}
              {product.occasion && (
                <Badge variant="outline" className="text-base px-3 py-1">{product.occasion}</Badge>
              )}
            </div>
          )}

          {/* Color selector */}
          {colors.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-800">
                Color — <span className="font-normal text-slate-500">{selectedColor}</span>
              </h3>
              <div className="flex gap-3 flex-wrap">
                {colors.map(color => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => { resetIdleTimer(); setSelectedColor(color); setSelectedSize(null); }}
                    className={`
                      h-16 px-6 rounded-2xl border-2 text-lg font-medium transition-all
                      ${selectedColor === color
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : 'border-slate-200 text-slate-600 hover:border-slate-400'}
                    `}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Size selector */}
          {selectedColor && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-800">Size</h3>
              <div className="flex flex-wrap gap-3">
                {['XS', 'S', 'M', 'L', 'XL', 'XXL', '28', '30', '32', '34', '36', '38', '40', '42']
                  .filter(s => availableSizes.includes(s))
                  .concat(availableSizes.filter(s => !['XS', 'S', 'M', 'L', 'XL', 'XXL', '28', '30', '32', '34', '36', '38', '40', '42'].includes(s)))
                  .filter((s, i, arr) => arr.indexOf(s) === i)
                  .map(size => (
                    <button
                      key={size}
                      type="button"
                      onClick={() => { resetIdleTimer(); setSelectedSize(size); }}
                      className={`
                        w-20 h-16 rounded-2xl border-2 text-xl font-bold transition-all
                        ${selectedSize === size
                          ? 'border-slate-900 bg-slate-900 text-white scale-105 shadow-lg'
                          : 'border-slate-200 text-slate-700 hover:border-slate-400'}
                      `}
                    >
                      {size}
                    </button>
                  ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Sticky CTA bar ─── */}
        <div className="p-6 border-t bg-white space-y-3">
          <Button
            type="button"
            size="lg"
            disabled={!selectedVariant || adding}
            onClick={handleAddToCart}
            className={`w-full h-20 text-2xl rounded-2xl gap-3 font-semibold transition-all ${
              addedVariantId
                ? 'bg-green-600 hover:bg-green-600'
                : 'bg-slate-900 hover:bg-slate-700'
            }`}
          >
            {adding ? (
              <Loader2 className="w-7 h-7 animate-spin" />
            ) : addedVariantId ? (
              <><Check className="w-7 h-7" /> Added!</>
            ) : (
              <><ShoppingBag className="w-7 h-7" /> Add to Cart</>
            )}
          </Button>

          <Button
            type="button"
            variant="outline"
            size="lg"
            className="w-full h-16 text-xl rounded-2xl gap-3 text-slate-600 border-slate-200"
            onClick={() => navigate('/kiosk/chat')}
          >
            <Sparkles className="w-5 h-5" />
            Ask Daksha AI about this
          </Button>
        </div>
      </div>
    </div>
  );
}
