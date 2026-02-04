import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useKiosk } from '../context/KioskSessionContext';
import { KioskService } from '@/lib/kioskApi';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowLeft, 
  ShoppingBag, 
  CheckCircle, 
  AlertCircle,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refreshCart } = useKiosk();

  const [product, setProduct] = useState(null);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  // Selection State
  const [selectedColor, setSelectedColor] = useState(null);
  const [selectedSize, setSelectedSize] = useState(null);
  const [selectedVariant, setSelectedVariant] = useState(null);

  // --- Fetch Data ---
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // 1. Get Product Details
        const productData = await KioskService.getProductDetail(id);
        setProduct(productData);

        // 2. Get Variants
        const variantsData = await KioskService.listVariants(id); // Using the listVariants from API
        if (Array.isArray(variantsData)) {
          setVariants(variantsData);
          
          // Auto-select first available color if exists
          const firstColor = variantsData.find(v => v.color)?.color;
          if (firstColor) setSelectedColor(firstColor);
        }
      } catch (error) {
        console.error("Failed to load product", error);
        toast.error("Could not load product details");
        navigate('/kiosk/catalog');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);

  // --- Determine Available Options ---
  // Get unique colors
  const colors = [...new Set(variants.map(v => v.color).filter(Boolean))];
  
  // Get available sizes for the selected color
  const availableSizes = variants
    .filter(v => v.color === selectedColor)
    .map(v => v.size)
    .filter(Boolean);

  // Update selected variant object when selection changes
  useEffect(() => {
    if (selectedColor && selectedSize) {
      const found = variants.find(v => v.color === selectedColor && v.size === selectedSize);
      setSelectedVariant(found);
    } else {
      setSelectedVariant(null);
    }
  }, [selectedColor, selectedSize, variants]);

  // --- Add to Cart ---
  const handleAddToCart = async () => {
    if (!selectedVariant) return;
    
    setAdding(true);
    try {
      await KioskService.addToCart(selectedVariant.id, 1);
      
      // Update global cart count
      await refreshCart();
      
      toast.success("Added to cart", {
        position: 'top-center',
        style: { fontSize: '1.2rem', padding: '1rem' }
      });
      
      navigate('/kiosk/catalog'); // Optional: Go back to shop or stay
    } catch (error) {
      toast.error("Failed to add to cart");
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-16 h-16 animate-spin text-slate-300" />
      </div>
    );
  }

  if (!product) return null;

  return (
    <div className="flex h-[calc(100vh-80px)] bg-white overflow-hidden">
      
      {/* Left: Image Gallery */}
      <div className="w-1/2 bg-slate-100 p-12 flex items-center justify-center relative">
        <Button 
          variant="ghost" 
          size="icon" 
          className="absolute top-8 left-8 h-16 w-16 rounded-full bg-white/80 hover:bg-white shadow-lg z-10"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft className="h-8 w-8 text-slate-900" />
        </Button>

        <img 
          src={product.images?.[0]?.image_url || "https://placehold.co/600x800"} 
          alt={product.name}
          className="max-h-full max-w-full object-contain drop-shadow-2xl hover:scale-105 transition-transform duration-500"
        />
      </div>

      {/* Right: Product Details */}
      <div className="w-1/2 p-12 overflow-y-auto flex flex-col">
        {/* Brand & Title */}
        <div className="space-y-4 mb-8">
          <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100 px-4 py-1 text-base">
            {product.brand}
          </Badge>
          <h1 className="text-5xl font-extrabold text-slate-900 leading-tight">
            {product.name}
          </h1>
          <div className="text-4xl font-bold text-primary">
            ₹{selectedVariant ? selectedVariant.base_price : (product.price || variants[0]?.base_price || 0)}
          </div>
        </div>

        {/* Description */}
        <p className="text-xl text-slate-500 leading-relaxed mb-12">
          {product.description}
        </p>

        {/* Variant Selectors */}
        <div className="space-y-10 mb-12">
          
          {/* Colors */}
          {colors.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-slate-900">Select Color</h3>
              <div className="flex gap-4">
                {colors.map(color => (
                  <button
                    key={color}
                    onClick={() => { setSelectedColor(color); setSelectedSize(null); }}
                    className={`
                      h-20 px-8 rounded-2xl border-2 text-xl font-medium transition-all
                      ${selectedColor === color 
                        ? 'border-primary bg-primary/5 text-primary ring-2 ring-primary/20' 
                        : 'border-slate-200 text-slate-600 hover:border-slate-400'}
                    `}
                  >
                    {color}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Sizes */}
          {selectedColor && (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-slate-900">Select Size</h3>
              <div className="flex flex-wrap gap-4">
                {['XS', 'S', 'M', 'L', 'XL', 'XXL'].map(size => {
                  const isAvailable = availableSizes.includes(size);
                  return (
                    <button
                      key={size}
                      disabled={!isAvailable}
                      onClick={() => setSelectedSize(size)}
                      className={`
                        w-20 h-20 rounded-full border-2 text-2xl font-bold flex items-center justify-center transition-all
                        ${!isAvailable ? 'opacity-30 cursor-not-allowed bg-slate-50 border-slate-100' : 
                          selectedSize === size 
                            ? 'border-primary bg-primary text-white shadow-xl scale-110' 
                            : 'border-slate-200 text-slate-700 hover:border-slate-400'}
                      `}
                    >
                      {size}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Action Bar (Sticky Bottom) */}
        <div className="mt-auto pt-8 border-t flex gap-6">
          <Button 
            size="lg"
            className="flex-1 h-24 text-2xl rounded-2xl shadow-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-50"
            disabled={!selectedVariant || adding}
            onClick={handleAddToCart}
          >
            {adding ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <>
                <ShoppingBag className="w-8 h-8 mr-4" />
                Add to Cart
              </>
            )}
          </Button>
        </div>

      </div>
    </div>
  );
}