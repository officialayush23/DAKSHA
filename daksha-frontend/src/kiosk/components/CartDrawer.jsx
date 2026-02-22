// import React, { useEffect, useState } from 'react';
// import { useNavigate } from 'react-router-dom';
// import { useKiosk } from '../context/KioskSessionContext';
// import { KioskService } from '@/lib/kioskApi';
// import { Button } from "@/components/ui/button";
// import { Card } from "@/components/ui/card";
// import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
// import { Trash2, ShoppingBag, ArrowRight, Loader2 } from 'lucide-react';
// import { toast } from 'sonner';

// export default function CartDrawer({ open, onClose }) {
//   const navigate = useNavigate();
//   const { sessionId, refreshCart } = useKiosk();
//   const [cartItems, setCartItems] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [removingId, setRemovingId] = useState(null);

//   useEffect(() => {
//     if (open) fetchCart();
//   }, [open]);

//   const fetchCart = async () => {
//     setLoading(true);
//     try {
//       const cart = await KioskService.getCart();
//       setCartItems(cart.items || []);
//     } catch (error) {
//       console.error("Cart load error", error);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleRemove = async (variantId) => {
//     setRemovingId(variantId);
//     try {
//       await KioskService.removeCartItem(variantId, sessionId);
//       await fetchCart();
//       await refreshCart();
//       toast.success("Item removed");
//     } catch (error) {
//       toast.error("Failed to remove item");
//     } finally {
//       setRemovingId(null);
//     }
//   };

//   const handleCheckout = () => {
//     onClose();
//     navigate('/kiosk/checkout');
//   };

//   const total = cartItems.reduce((acc, item) => acc + (item.price * item.quantity), 0);

//   return (
//     <Sheet open={open} onOpenChange={onClose}>
//       <SheetContent side="right" className="w-full sm:max-w-lg p-0 flex flex-col">
//         <SheetHeader className="p-8 border-b">
//           <SheetTitle className="text-3xl font-bold flex items-center gap-3">
//             <ShoppingBag className="w-8 h-8" />
//             Your Cart
//           </SheetTitle>
//         </SheetHeader>

//         <div className="flex-1 overflow-y-auto p-6 space-y-4">
//           {loading ? (
//             <div className="h-64 flex items-center justify-center">
//               <Loader2 className="h-10 w-10 animate-spin text-slate-300" />
//             </div>
//           ) : cartItems.length === 0 ? (
//             <div className="h-64 flex flex-col items-center justify-center text-slate-400 space-y-4">
//               <ShoppingBag className="w-16 h-16 opacity-20" />
//               <p className="text-xl">Your cart is empty</p>
//               <Button variant="outline" size="lg" onClick={onClose} className="text-lg h-14 px-8 rounded-full">
//                 Continue Shopping
//               </Button>
//             </div>
//           ) : (
//             cartItems.map(item => (
//               <Card key={item.id} className="p-5 flex items-center gap-5 shadow-sm">
//                 <div className="h-20 w-20 bg-slate-100 rounded-xl overflow-hidden shrink-0">
//                   <img
//                     src={item.image || "https://placehold.co/80"}
//                     alt=""
//                     className="h-full w-full object-cover"
//                   />
//                 </div>
//                 <div className="flex-1 min-w-0">
//                   <h3 className="text-lg font-bold text-slate-900 truncate">{item.product_name}</h3>
//                   <p className="text-base text-slate-500">Qty: {item.quantity}</p>
//                   <p className="text-lg font-bold text-primary mt-1">
//                     ₹{(item.price * item.quantity).toFixed(0)}
//                   </p>
//                 </div>
//                 <Button
//                   variant="ghost"
//                   size="icon"
//                   className="text-red-400 hover:text-red-600 hover:bg-red-50 shrink-0 h-12 w-12"
//                   onClick={() => handleRemove(item.product_variant_id)}
//                   disabled={removingId === item.product_variant_id}
//                 >
//                   {removingId === item.product_variant_id ? (
//                     <Loader2 className="h-5 w-5 animate-spin" />
//                   ) : (
//                     <Trash2 className="h-5 w-5" />
//                   )}
//                 </Button>
//               </Card>
//             ))
//           )}
//         </div>

//         {cartItems.length > 0 && (
//           <div className="p-6 border-t space-y-4 bg-white">
//             <div className="flex justify-between items-center text-2xl font-bold text-slate-900">
//               <span>Total</span>
//               <span>₹{total.toFixed(0)}</span>
//             </div>
//             <Button
//               size="lg"
//               className="w-full h-16 text-xl rounded-2xl bg-green-600 hover:bg-green-700 shadow-lg"
//               onClick={handleCheckout}
//             >
//               Proceed to Checkout <ArrowRight className="ml-3 w-6 h-6" />
//             </Button>
//           </div>
//         )}
//       </SheetContent>
//     </Sheet>
//   );
// }