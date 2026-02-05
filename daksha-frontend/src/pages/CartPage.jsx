import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CartService } from '../lib/api';
import { Button } from "@/components/ui/button";
import { Link } from 'react-router-dom';
import { Loader2, Trash2, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

export default function CartPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['cart'],
    queryFn: () => CartService.get().then(res => res.data), // Axios returns data object
  });

  const removeItem = useMutation({
    mutationFn: CartService.remove,
    onSuccess: () => {
      queryClient.invalidateQueries(['cart']);
      toast.success("Item removed");
    }
  });

  if (isLoading) return <div className="h-96 flex items-center justify-center"><Loader2 className="animate-spin"/></div>;

  const items = data?.items || [];
  const subtotal = items.reduce((acc, item) => acc + (item.price * item.quantity), 0);

  if (items.length === 0) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center text-center space-y-6">
        <h2 className="text-3xl font-serif">Your bag is empty</h2>
        <Link to="/dash/shop">
          <Button size="lg" className="rounded-full px-8">Start Shopping</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-4xl font-serif font-bold mb-8">Shopping Bag</h1>
      
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Items List */}
        <div className="lg:col-span-2 space-y-6">
          {items.map(item => (
            <div key={item.variant_id} className="flex gap-6 p-4 bg-white rounded-2xl border border-zinc-100 shadow-sm">
              <div className="w-24 h-32 bg-zinc-100 rounded-xl overflow-hidden shrink-0">
                {/* Image Placeholder */}
                <div className="w-full h-full bg-zinc-200" /> 
              </div>
              <div className="flex-1 flex flex-col justify-between py-2">
                <div>
                  <h3 className="font-bold text-lg">{item.variant?.product?.name || "Product Item"}</h3>
                  <p className="text-sm text-zinc-500">Size: {item.variant?.size} • SKU: {item.sku}</p>
                </div>
                <div className="flex justify-between items-end">
                  <div className="text-xl font-medium">₹{item.price}</div>
                  <button 
                    onClick={() => removeItem.mutate(item.variant_id)}
                    className="text-red-500 hover:text-red-600 text-sm flex items-center gap-1"
                  >
                    <Trash2 size={16} /> Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white p-6 rounded-3xl border border-zinc-100 sticky top-24 shadow-xl shadow-zinc-200/50">
            <h3 className="text-xl font-bold mb-6">Summary</h3>
            <div className="space-y-4 mb-8">
              <div className="flex justify-between text-zinc-600">
                <span>Subtotal</span>
                <span>₹{subtotal}</span>
              </div>
              <div className="flex justify-between text-zinc-600">
                <span>Shipping</span>
                <span className="text-emerald-600">Free</span>
              </div>
              <div className="pt-4 border-t border-zinc-100 flex justify-between font-bold text-xl">
                <span>Total</span>
                <span>₹{subtotal}</span>
              </div>
            </div>
            
            <Link to="/dash/checkout">
              <Button className="w-full h-14 rounded-full text-lg shadow-lg hover:shadow-xl transition-all">
                Checkout <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}