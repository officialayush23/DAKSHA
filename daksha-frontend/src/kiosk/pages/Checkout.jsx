// import React, { useEffect, useState } from 'react';
// import { useNavigate } from 'react-router-dom';
// import { useKiosk } from '../context/KioskSessionContext';
// import { KioskService } from '@/lib/kioskApi';
// import { Button } from "@/components/ui/button";
// import { Card } from "@/components/ui/card";
// import {
//   ArrowLeft,
//   Trash2,
//   CreditCard,
//   QrCode,
//   CheckCircle,
//   Loader2
// } from 'lucide-react';
// import { toast } from 'sonner';

// export default function Checkout() {
//   const navigate = useNavigate();
//   const { refreshCart, user, endSession, sessionId } = useKiosk(); // FIX: sessionId from context

//   const [cartItems, setCartItems] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [processing, setProcessing] = useState(false);
//   const [orderComplete, setOrderComplete] = useState(false);
//   const [paymentMethod, setPaymentMethod] = useState('card');

//   useEffect(() => {
//     fetchCart();
//   }, []);

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
//     try {
//       // FIX: pass sessionId to removeCartItem
//       await KioskService.removeCartItem(variantId, sessionId);
//       fetchCart();
//       refreshCart();
//       toast.success("Item removed");
//     } catch (error) {
//       toast.error("Failed to remove item");
//     }
//   };

//   const calculateTotal = () => {
//     return cartItems.reduce((acc, item) => acc + (item.price * item.quantity), 0);
//   };

//   const handlePayment = async () => {
//     setProcessing(true);
//     try {
//       const checkout = await KioskService.startCheckout();
//       await new Promise(resolve => setTimeout(resolve, 3000));
//       await KioskService.processPayment(checkout.id);
//       setOrderComplete(true);
//       toast.success("Payment Successful!");
//       setTimeout(() => {
//         endSession("Order completed. Thank you!");
//       }, 5000);
//     } catch (error) {
//       console.error("Checkout failed", error);
//       toast.error("Payment failed. Please try again.");
//       setProcessing(false);
//     }
//   };

//   if (orderComplete) {
//     return (
//       <div className="h-full flex flex-col items-center justify-center bg-green-50 text-center p-8">
//         <div className="h-32 w-32 bg-green-100 rounded-full flex items-center justify-center mb-8 animate-bounce">
//           <CheckCircle className="h-16 w-16 text-green-600" />
//         </div>
//         <h1 className="text-5xl font-bold text-green-900 mb-4">Order Confirmed!</h1>
//         <p className="text-2xl text-green-700 mb-12">
//           Please collect your receipt. Your items will be ready at the counter.
//         </p>
//         <Button
//           size="lg"
//           onClick={() => endSession("New Session")}
//           className="h-20 px-12 text-2xl rounded-full"
//         >
//           Start New Order
//         </Button>
//       </div>
//     );
//   }

//   return (
//     <div className="flex h-[calc(100vh-80px)] bg-slate-50">

//       {/* Left: Cart Items */}
//       <div className="w-2/3 p-8 overflow-y-auto">
//         <div className="flex items-center gap-4 mb-8">
//           <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
//             <ArrowLeft className="h-8 w-8" />
//           </Button>
//           <h1 className="text-4xl font-bold text-slate-900">Your Cart</h1>
//         </div>

//         {loading ? (
//           <div className="h-64 flex items-center justify-center">
//             <Loader2 className="h-12 w-12 animate-spin text-slate-300" />
//           </div>
//         ) : cartItems.length === 0 ? (
//           <div className="h-64 flex flex-col items-center justify-center text-slate-400">
//             <p className="text-2xl">Your cart is empty</p>
//             <Button variant="link" onClick={() => navigate('/kiosk/catalog')} className="text-xl mt-4">
//               Start Shopping
//             </Button>
//           </div>
//         ) : (
//           <div className="space-y-6">
//             {cartItems.map(item => (
//               <Card key={item.id} className="p-6 flex items-center gap-6 shadow-sm">
//                 <div className="h-24 w-24 bg-slate-100 rounded-lg overflow-hidden">
//                   <img src={item.image || "https://placehold.co/100"} alt="" className="h-full w-full object-cover" />
//                 </div>
//                 <div className="flex-1">
//                   <h3 className="text-xl font-bold text-slate-900">{item.product_name}</h3>
//                   <p className="text-lg text-slate-500">Qty: {item.quantity} • {item.variant_name}</p>
//                 </div>
//                 <div className="text-right">
//                   <div className="text-2xl font-bold text-slate-900">
//                     ₹{(item.price * item.quantity).toFixed(0)}
//                   </div>
//                   <Button
//                     variant="ghost"
//                     size="sm"
//                     className="text-red-500 hover:text-red-600 hover:bg-red-50 mt-2"
//                     onClick={() => handleRemove(item.product_variant_id)}
//                   >
//                     <Trash2 className="h-5 w-5 mr-1" /> Remove
//                   </Button>
//                 </div>
//               </Card>
//             ))}
//           </div>
//         )}
//       </div>

//       {/* Right: Payment Sidebar */}
//       <div className="w-1/3 bg-white border-l p-8 flex flex-col shadow-2xl z-10">

//         {user && (
//           <div className="mb-8 p-4 bg-blue-50 rounded-xl border border-blue-100">
//             <div className="text-sm text-blue-600 font-bold uppercase tracking-wide mb-1">Logged In As</div>
//             <div className="text-xl font-bold text-blue-900">{user.name}</div>
//             <div className="text-blue-700">{user.email}</div>
//           </div>
//         )}

//         <div className="space-y-6 flex-1">
//           <h2 className="text-2xl font-bold">Payment Method</h2>
//           <div className="grid grid-cols-2 gap-4">
//             <button
//               onClick={() => setPaymentMethod('card')}
//               className={`h-32 rounded-xl border-2 flex flex-col items-center justify-center gap-3 transition-all ${
//                 paymentMethod === 'card' ? 'border-primary bg-primary/5 text-primary' : 'border-slate-200 text-slate-500'
//               }`}
//             >
//               <CreditCard className="h-10 w-10" />
//               <span className="font-bold text-lg">Card / NFC</span>
//             </button>
//             <button
//               onClick={() => setPaymentMethod('upi')}
//               className={`h-32 rounded-xl border-2 flex flex-col items-center justify-center gap-3 transition-all ${
//                 paymentMethod === 'upi' ? 'border-primary bg-primary/5 text-primary' : 'border-slate-200 text-slate-500'
//               }`}
//             >
//               <QrCode className="h-10 w-10" />
//               <span className="font-bold text-lg">UPI QR</span>
//             </button>
//           </div>
//         </div>

//         <div className="mt-auto space-y-6 pt-8 border-t">
//           <div className="flex justify-between items-center text-xl text-slate-500">
//             <span>Subtotal</span>
//             <span>₹{calculateTotal().toFixed(0)}</span>
//           </div>
//           <div className="flex justify-between items-center text-3xl font-bold text-slate-900">
//             <span>Total</span>
//             <span>₹{calculateTotal().toFixed(0)}</span>
//           </div>

//           <Button
//             size="lg"
//             className="w-full h-24 text-3xl font-bold rounded-2xl shadow-xl bg-green-600 hover:bg-green-700 hover:scale-[1.02] transition-transform"
//             onClick={handlePayment}
//             disabled={cartItems.length === 0 || processing}
//           >
//             {processing ? (
//               <>
//                 <Loader2 className="mr-4 h-8 w-8 animate-spin" />
//                 Processing...
//               </>
//             ) : (
//               "Pay Now"
//             )}
//           </Button>
//         </div>
//       </div>
//     </div>
//   );
// }