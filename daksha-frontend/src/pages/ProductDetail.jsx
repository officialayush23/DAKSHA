import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ProductService, CartService, UserService, RecommendationService, SessionService } from '../lib/api';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ShoppingBag, Heart, Star } from 'lucide-react';
import { toast } from 'sonner';

export default function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [boughtTogether, setBoughtTogether] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Parallel fetch for speed
      const [prodData, simData, btData] = await Promise.all([
        ProductService.getDetail(id),
        RecommendationService.getSimilarVariants(id).catch(() => []), // Soft fail on recs
        RecommendationService.getBoughtTogether(id).catch(() => [])
      ]);
      
      setProduct(prodData);
      setSimilar(simData || []);
      setBoughtTogether(btData || []);
      
      if (prodData?.variants?.length > 0) {
        setSelectedVariant(prodData.variants[0]);
      }
    } catch (error) {
      toast.error("Failed to load product");
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!selectedVariant) return;
    setAdding(true);
    try {
      const activeSession = await SessionService.getActive();
      const sessionId = activeSession?.data?.session_id;
      
      if (!sessionId) {
        toast.error("Session missing. Refresh page.");
        return;
      }

      await CartService.add(selectedVariant.variant_id, 1, sessionId);
      toast.success("Added to Bag");
    } catch (error) {
      toast.error("Failed to add to bag");
    } finally {
      setAdding(false);
    }
  };

  const handleWishlist = async () => {
    if (!selectedVariant) return;
    try {
      await UserService.addToWishlist(selectedVariant.variant_id);
      toast.success("Saved to Wishlist");
    } catch (error) {
      toast.error("Already in wishlist or error");
    }
  };

  if (loading) return <div className="h-screen flex items-center justify-center"><Loader2 className="animate-spin" /></div>;
  if (!product) return <div>Product not found</div>;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
      {/* Images */}
      <div className="space-y-4">
        <div className="aspect-[3/4] bg-zinc-100 rounded-2xl overflow-hidden shadow-sm">
          <img 
            src={selectedVariant?.images?.[0] || product.image || "https://placehold.co/600x800"} 
            alt={product.name}
            className="w-full h-full object-cover"
          />
        </div>
      </div>

      {/* Info */}
      <div className="space-y-8 py-8">
        <div>
          <h2 className="text-sm font-bold text-zinc-400 uppercase tracking-widest mb-2">{product.brand}</h2>
          <h1 className="text-4xl md:text-5xl font-serif font-bold text-zinc-900 mb-4">{product.name}</h1>
          <div className="flex items-center gap-4">
            <span className="text-3xl font-light">₹{selectedVariant?.final_price || selectedVariant?.base_price}</span>
            {selectedVariant?.offer && (
              <Badge className="bg-red-50 text-red-600 hover:bg-red-100 border-red-100">
                {selectedVariant.offer}
              </Badge>
            )}
          </div>
        </div>

        <p className="text-zinc-600 leading-relaxed text-lg">{product.description}</p>

        {/* Variants */}
        <div className="space-y-4">
          <span className="text-sm font-medium text-zinc-900">Select Variant</span>
          <div className="flex flex-wrap gap-3">
            {product.variants.map(v => (
              <button
                key={v.variant_id}
                onClick={() => setSelectedVariant(v)}
                className={`
                  h-12 px-4 rounded-lg border flex items-center justify-center text-sm font-medium transition-all
                  ${selectedVariant?.variant_id === v.variant_id 
                    ? 'border-black bg-black text-white' 
                    : 'border-zinc-200 text-zinc-600 hover:border-zinc-400'}
                `}
              >
                {v.color} - {v.size}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4 pt-4">
          <Button 
            size="lg" 
            className="flex-1 h-16 rounded-full text-lg gap-3" 
            onClick={handleAddToCart}
            disabled={adding}
          >
            {adding ? <Loader2 className="animate-spin" /> : <ShoppingBag />}
            Add to Bag
          </Button>
          <Button 
            size="lg" 
            variant="outline" 
            className="h-16 w-16 rounded-full p-0 border-zinc-200"
            onClick={handleWishlist}
          >
            <Heart />
          </Button>
        </div>

        {/* Bought Together */}
        {boughtTogether.length > 0 && (
          <div className="pt-12 border-t border-zinc-100">
            <h3 className="text-xl font-serif font-bold mb-6">Frequently Bought Together</h3>
            <div className="flex gap-4 overflow-x-auto no-scrollbar pb-4">
              {boughtTogether.map(p => (
                <Link key={p.variant_id} to={`/dash/product/${p.product_id}`} className="min-w-[140px] block group">
                  <div className="aspect-[3/4] bg-zinc-100 rounded-lg overflow-hidden mb-2">
                    <div className="w-full h-full bg-zinc-200" />
                  </div>
                  <p className="text-sm font-medium truncate group-hover:underline">₹{p.final_price}</p>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}