// src/pages/ProductDetail.jsx
import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Heart, ShoppingBag, ArrowLeft, Star, Truck, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { ProductService, CartService } from '../lib/api';

export default function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVariant, setSelectedVariant] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Parallel Fetch
        const [prodRes, simRes, revRes] = await Promise.all([
          ProductService.getDetail(id),
          ProductService.getSimilar(id),
          ProductService.getReviews(id)
        ]);

        setProduct(prodRes.data);
        setSimilar(simRes.data);
        setReviews(revRes.data);

        if(prodRes.data?.variants?.length > 0) {
            setSelectedVariant(prodRes.data.variants[0]);
        }
      } catch (err) {
        toast.error("Product unavailable");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleAddToCart = async () => {
    if (!selectedVariant) return;
    try {
      await CartService.add(selectedVariant.variant_id, 1);
      toast.success("Added to Bag");
    } catch (err) {
      toast.error("Login required");
    }
  };

  if (loading) return <div className="h-96 flex items-center justify-center font-serif text-2xl animate-pulse">Loading Masterpiece...</div>;
  if (!product) return <div>Not Found</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-24">
      {/* Top Section */}
      <div className="flex flex-col lg:flex-row gap-12">
        {/* Gallery */}
        <div className="w-full lg:w-1/2 space-y-4">
          <div className="aspect-[3/4] bg-gray-100 overflow-hidden">
            <img 
              src={selectedVariant?.images?.[0] || "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&q=80"} 
              className="w-full h-full object-cover" 
            />
          </div>
        </div>

        {/* Info */}
        <div className="w-full lg:w-1/2 flex flex-col justify-center">
          <div className="border-b border-gray-100 pb-8 mb-8">
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-gray-400 mb-3">{product.brand}</h2>
            <h1 className="text-5xl font-serif mb-4 leading-tight">{product.name || product.description}</h1>
            <div className="flex items-center gap-6">
                <span className="text-3xl font-light">₹{selectedVariant?.price || 0}</span>
                <div className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded text-xs font-bold">
                    <Star size={12} className="fill-black" /> {product.rating || 4.5}
                </div>
            </div>
          </div>

          <div className="mb-10 space-y-4">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Size</p>
            <div className="flex gap-2">
              {product.variants.map(v => (
                <button
                  key={v.variant_id}
                  onClick={() => setSelectedVariant(v)}
                  className={`w-10 h-10 border text-xs font-medium transition-all
                    ${selectedVariant?.variant_id === v.variant_id ? 'bg-black text-white border-black' : 'hover:border-black'}
                  `}
                >
                  {v.size}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-4">
            <button onClick={handleAddToCart} className="flex-1 bg-black text-white h-14 uppercase text-xs font-bold tracking-widest hover:bg-zinc-800 transition-colors">
              Add to Bag
            </button>
            <button className="w-14 border border-gray-200 flex items-center justify-center hover:border-black transition-colors">
              <Heart size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Similar Products */}
      {similar.length > 0 && (
        <section>
          <h3 className="font-serif text-3xl mb-8">You May Also Like</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {similar.slice(0, 4).map(p => (
              <Link to={`/dash/product/${p.id}`} key={p.id} className="group block">
                <div className="aspect-[3/4] bg-gray-100 mb-4 overflow-hidden">
                  <img src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&q=80" className="w-full h-full object-cover bw-image group-hover:scale-105 transition-transform" />
                </div>
                <h4 className="font-serif text-lg">{p.brand}</h4>
                <p className="text-xs text-gray-400 uppercase">{p.category}</p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}