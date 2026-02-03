import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Heart, ShoppingBag, ArrowLeft, Star } from 'lucide-react';
import { toast } from 'sonner';
import { UserService, CartService } from '../lib/api';

export default function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSize, setSelectedSize] = useState("");

  useEffect(() => {
    // In a real app, you'd fetch by ID. 
    // For now, we simulate fetching or reuse the product list logic.
    const fetchProduct = async () => {
      try {
        // const res = await UserService.getProduct(id); 
        // setProduct(res.data);
        
        // Mock Data for now until specific endpoint is ready
        setTimeout(() => {
            setProduct({
                product_id: id,
                brand: "Daksha Luxury",
                description: "Handcrafted Italian Silk Blouse",
                price: 12000,
                image: "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&q=80",
                variants: ["S", "M", "L", "XL"],
                reviews: 128,
                rating: 4.8
            });
            setLoading(false);
        }, 800);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    };
    fetchProduct();
  }, [id]);

  const handleAddToCart = async () => {
    if (!selectedSize) {
      toast.error("Please select a size");
      return;
    }
    try {
      await CartService.addItem(product.product_id, 1, "session-123");
      toast.success("Added to Bag");
    } catch (err) {
        // Fallback for demo if backend isn't perfectly synced yet
      toast.success("Added to Bag (Demo)");
    }
  };

  if (loading) return (
    <div className="min-h-screen p-6 md:p-12 flex flex-col md:flex-row gap-12 max-w-7xl mx-auto">
        <div className="w-full md:w-1/2 aspect-[3/4] skeleton" />
        <div className="w-full md:w-1/2 space-y-6">
            <div className="skeleton h-12 w-3/4" />
            <div className="skeleton h-6 w-1/4" />
            <div className="skeleton h-32 w-full" />
        </div>
    </div>
  );

  if (!product) return <div className="text-center py-20">Product not found</div>;

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto p-6 md:p-12">
        <Link to="/shop" className="inline-flex items-center gap-2 text-gray-500 hover:text-black mb-8 transition-colors">
          <ArrowLeft size={20} /> Back to Shop
        </Link>

        <div className="flex flex-col md:flex-row gap-12 lg:gap-20">
          {/* Image Section */}
          <div className="w-full md:w-1/2">
            <div className="aspect-[3/4] bg-gray-100 overflow-hidden relative">
              <img 
                src={product.image} 
                alt={product.description} 
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Details Section */}
          <div className="w-full md:w-1/2 flex flex-col justify-center">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500 mb-2">{product.brand}</h2>
            <h1 className="text-4xl md:text-5xl font-serif mb-4">{product.description}</h1>
            
            <div className="flex items-center gap-4 mb-8">
              <span className="text-2xl font-medium font-sans">₹{product.price}</span>
              <div className="flex items-center gap-1 text-sm">
                <Star className="w-4 h-4 fill-daksha-accent text-daksha-accent" />
                <span>{product.rating} ({product.reviews} reviews)</span>
              </div>
            </div>

            {/* Size Selector */}
            <div className="mb-10">
              <p className="text-xs font-bold uppercase tracking-widest mb-4">Select Size</p>
              <div className="flex gap-4">
                {product.variants.map(size => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`w-12 h-12 border flex items-center justify-center transition-all ${
                      selectedSize === size 
                        ? 'border-daksha-black bg-daksha-black text-white' 
                        : 'border-gray-200 hover:border-gray-400'
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button 
                onClick={handleAddToCart}
                className="flex-1 bg-daksha-black text-white py-4 uppercase tracking-widest text-sm hover:bg-daksha-accent transition-colors flex items-center justify-center gap-3"
              >
                <ShoppingBag size={18} /> Add to Bag
              </button>
              <button className="p-4 border border-gray-200 hover:border-red-500 hover:text-red-500 transition-colors">
                <Heart size={20} />
              </button>
            </div>

            {/* Additional Info */}
            <div className="mt-12 space-y-4 border-t border-gray-100 pt-8 text-sm text-gray-500">
              <div className="flex justify-between">
                <span>Fabric</span>
                <span className="text-black">100% Organic Silk</span>
              </div>
              <div className="flex justify-between">
                <span>Care</span>
                <span className="text-black">Dry Clean Only</span>
              </div>
              <div className="flex justify-between">
                <span>Shipping</span>
                <span className="text-black">Free Standard Shipping</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}