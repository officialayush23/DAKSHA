import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, ShoppingBag, Filter } from 'lucide-react';
import { toast } from 'sonner';
import { UserService, CartService } from '../lib/api';

// --- COMPONENTS ---
const FilterSidebar = ({ onFilter }) => (
  <div className="w-64 hidden md:block p-6 border-r border-gray-100 h-[calc(100vh-80px)] sticky top-20">
    <h3 className="font-serif text-2xl mb-6">Filters</h3>
    {/* Simple Categories */}
    <div className="space-y-4">
      <p className="font-bold text-xs uppercase tracking-widest text-gray-400">Category</p>
      {['Ethnic', 'Casual', 'Formal', 'Streetwear'].map(cat => (
        <label key={cat} className="flex items-center gap-3 cursor-pointer group">
          <input type="checkbox" className="accent-daksha-black" onChange={() => onFilter('category', cat)} />
          <span className="text-sm group-hover:text-daksha-accent transition-colors">{cat}</span>
        </label>
      ))}
    </div>
    {/* Price Slider Placeholder */}
    <div className="mt-8 space-y-4">
      <p className="font-bold text-xs uppercase tracking-widest text-gray-400">Price Range</p>
      <input type="range" min="0" max="10000" className="w-full accent-daksha-black" onChange={(e) => onFilter('max_price', e.target.value)}/>
    </div>
  </div>
);

const ShopProductCard = ({ product }) => {
  const handleAddToCart = async (e) => {
    e.preventDefault();
    try {
      await CartService.addItem(product.variant_id, 1, "session-123"); // Replace session with real ID
      toast.success(`${product.brand} added to cart`);
    } catch (err) {
      toast.error("Please login to add items");
    }
  };

  const handleWishlist = (e) => {
    e.preventDefault();
    // Wishlist API call here
    toast("Added to Wishlist", { icon: '❤️' });
  };

  return (
    <Link to={`/product/${product.product_id}`} className="group block relative">
      <div className="aspect-[3/4] bg-gray-100 overflow-hidden relative">
        <img 
          src={product.image || "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&q=80"} 
          alt={product.brand}
          className="w-full h-full object-cover bw-image group-hover:scale-105"
        />
        
        {/* Offer Badge */}
        {product.offer && (
          <div className="absolute top-0 left-0 bg-daksha-black text-white text-[10px] font-bold px-2 py-1 uppercase tracking-widest">
            {product.offer.label}
          </div>
        )}

        {/* Hover Actions */}
        <div className="absolute bottom-4 right-4 flex flex-col gap-2 translate-y-10 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300">
          <button onClick={handleWishlist} className="bg-white p-3 rounded-full shadow-lg hover:text-red-500 transition-colors">
            <Heart size={18} />
          </button>
          <button onClick={handleAddToCart} className="bg-daksha-black text-white p-3 rounded-full shadow-lg hover:bg-daksha-accent transition-colors">
            <ShoppingBag size={18} />
          </button>
        </div>
      </div>

      <div className="mt-4 flex justify-between items-start">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-widest text-gray-500">{product.brand}</h3>
          <p className="font-serif text-lg leading-none mt-1">{product.description || "Luxury Garment"}</p>
        </div>
        <div className="text-right">
          {product.offer ? (
            <>
              <p className="text-xs line-through text-gray-400">₹{product.price}</p>
              <p className="font-bold">₹{product.price * 0.8}</p> {/* Mock calc */}
            </>
          ) : (
            <p className="font-bold">₹{product.price}</p>
          )}
        </div>
      </div>
    </Link>
  );
};

export default function ShopPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Determine if we show Feed (Recommendations) or Catalog
    const fetchProducts = async () => {
      try {
        const res = await UserService.getProducts({}); // Or getRecommendationFeed()
        setProducts(res.data);
      } catch (err) {
        console.error(err);
        toast.error("Failed to load products");
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  return (
    <div className="flex bg-white min-h-screen">
      <FilterSidebar onFilter={(k, v) => console.log(k, v)} />
      
      <div className="flex-1 p-6 md:p-12">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-serif">All Products</h1>
          <button className="md:hidden flex gap-2 text-sm uppercase tracking-widest border border-black px-4 py-2">
            <Filter size={16} /> Filters
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-8">
            {[1,2,3,4,5,6].map(i => (
              <div key={i} className="space-y-4">
                <div className="skeleton h-[400px] w-full" />
                <div className="skeleton h-4 w-1/2" />
                <div className="skeleton h-4 w-1/4" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-12">
            {products.map((p, i) => <ShopProductCard key={i} product={p} />)}
          </div>
        )}
      </div>
    </div>
  );
}