import React, { useState, useEffect, useRef } from "react";
import { useOutletContext } from "react-router-dom"; // Need context for store_id if passing from layout
import api from "@/lib/apiClient";
import { Mic, Send, MapPin, ShoppingCart, User, Volume2, VolumeX, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { supabase } from "@/lib/supabaseClient";

export default function StoreGuide() {
  // HARDCODED STORE ID FOR DEMO (Or fetch from URL/Context)
  // In production, the Kiosk device ID determines this.
  const STORE_ID = "d86ab247-564c-4f1e-a581-e0a2577af59e"; 

  const [messages, setMessages] = useState([
    { role: 'ai', content: "Welcome! I'm your store guide. Ask me where to find any item, or check your cart locations." }
  ]);
  const [input, setInput] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const [view, setView] = useState("chat"); // chat | cart

  const messagesEndRef = useRef(null);

  // --- SCROLL TO BOTTOM ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --- TTS HELPER ---
  const speak = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Stop previous
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  // --- STT HELPER ---
  const toggleListening = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert("Voice input not supported in this browser.");
      return;
    }

    if (isListening) {
      setIsListening(false); // Stop (logic handled by onend usually)
      return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => setIsListening(true);
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      handleSend(transcript); // Auto-send on voice end
    };

    recognition.onend = () => setIsListening(false);
    recognition.start();
  };

  // --- CHAT LOGIC ---
  const handleSend = async (textOverride = null) => {
    const query = textOverride || input;
    if (!query.trim()) return;

    // 1. Add User Message
    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setInput("");

    try {
      // 2. Call Backend
      const res = await api.post("/kiosk/chat", {
        message: query,
        store_id: STORE_ID
      });

      const { response, products } = res.data;

      // 3. Add AI Message with Product Cards
      const aiMsg = { 
        role: 'ai', 
        content: response, 
        products: products 
      };
      setMessages(prev => [...prev, aiMsg]);
      
      // 4. Speak Response
      speak(response);

    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: "I'm having trouble connecting to the inventory system right now." }]);
    }
  };

  // --- LOAD CART MAP ---
  const loadCartMap = async () => {
    setView("cart");
    try {
      const res = await api.get(`/kiosk/cart/map/${STORE_ID}`);
      setCartItems(res.data);
      if(res.data.length > 0) {
          speak(`You have ${res.data.length} items in your cart. Here is where to find them.`);
      } else {
          speak("Your cart is empty.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="h-screen bg-black text-white flex flex-col font-sans overflow-hidden">
      
      {/* NAVBAR */}
      <header className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-950/80 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-white rounded-full flex items-center justify-center">
            <span className="text-black font-bold text-xl">Ai</span>
          </div>
          <div>
            <h1 className="font-bold text-lg leading-none">Store Guide</h1>
            <p className="text-xs text-zinc-400">Pune Branch • Online</p>
          </div>
        </div>
        
        <div className="flex gap-4">
          <Button 
            variant={view === "chat" ? "default" : "outline"}
            onClick={() => setView("chat")}
            className={view === "chat" ? "bg-white text-black" : "border-zinc-800 text-zinc-400"}
          >
            Assistant
          </Button>
          <Button 
            variant={view === "cart" ? "default" : "outline"}
            onClick={loadCartMap}
            className={view === "cart" ? "bg-emerald-600 text-white hover:bg-emerald-700" : "border-zinc-800 text-zinc-400"}
          >
            <ShoppingCart className="mr-2 h-4 w-4" /> Locate Cart
          </Button>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="flex-1 relative">
        
        {view === "chat" ? (
          <ScrollArea className="h-full px-4 md:px-20 py-6">
            <div className="space-y-6 pb-24 max-w-4xl mx-auto">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user' ? 'bg-zinc-800 text-white rounded-tr-none' : 'bg-white text-black rounded-tl-none shadow-xl'}`}>
                    <p className="text-lg leading-relaxed">{msg.content}</p>
                    
                    {/* PRODUCT CARDS IN CHAT */}
                    {msg.products && msg.products.length > 0 && (
                      <div className="mt-4 grid gap-3">
                        {msg.products.map((prod, pIdx) => (
                          <div key={pIdx} className="flex gap-4 bg-zinc-100 p-3 rounded-xl border border-zinc-200">
                            <div className="h-20 w-20 bg-white rounded-lg border border-zinc-200 overflow-hidden flex-shrink-0">
                                <img src={prod.image || "https://placehold.co/100"} className="h-full w-full object-cover"/>
                            </div>
                            <div className="flex flex-col justify-center">
                                <h4 className="font-bold text-black">{prod.name}</h4>
                                <p className="text-sm text-zinc-600">{prod.variant}</p>
                                <div className="mt-1 flex items-center gap-2">
                                    <Badge className="bg-black text-white hover:bg-zinc-800">
                                        <MapPin className="h-3 w-3 mr-1" /> Aisle {prod.location.aisle || "?"}
                                    </Badge>
                                    <span className="text-sm font-bold text-emerald-600">Shelf {prod.location.shelf || "?"}</span>
                                </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        ) : (
          /* CART VIEW */
          <div className="h-full p-6 md:p-10 overflow-y-auto">
             <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
                {cartItems.map((item, idx) => (
                    <Card key={idx} className="bg-zinc-900 border-zinc-800 text-white flex overflow-hidden">
                        <div className="w-32 bg-white flex items-center justify-center p-2">
                            <img src={item.image} className="max-h-full object-contain mix-blend-multiply" />
                        </div>
                        <div className="p-4 flex-1 flex flex-col justify-between">
                            <div>
                                <h3 className="font-bold text-lg">{item.product_name}</h3>
                                <p className="text-zinc-400 text-sm">{item.variant_info}</p>
                            </div>
                            
                            <div className="flex items-end justify-between mt-4">
                                <div>
                                    <p className="text-xs text-zinc-500 uppercase font-bold">Location</p>
                                    <div className="flex items-center gap-2 text-xl font-mono text-emerald-400">
                                        <MapPin className="h-5 w-5" />
                                        Aisle {item.aisle || "?"} <span className="text-zinc-600 text-sm">/</span> Shelf {item.shelf || "?"}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className="block text-xs text-zinc-500">Qty: {item.cart_qty}</span>
                                    {item.in_stock_here ? (
                                        <Badge className="bg-emerald-950 text-emerald-400 border-emerald-900">In Stock</Badge>
                                    ) : (
                                        <Badge className="bg-red-950 text-red-400 border-red-900">Out of Stock</Badge>
                                    )}
                                </div>
                            </div>
                        </div>
                    </Card>
                ))}
                {cartItems.length === 0 && (
                    <div className="col-span-full text-center py-20 text-zinc-500">
                        <ShoppingCart className="h-16 w-16 mx-auto mb-4 opacity-20" />
                        <p className="text-xl">Your cart is empty.</p>
                    </div>
                )}
             </div>
          </div>
        )}

      </main>

      {/* INPUT BAR (Chat View Only) */}
      {view === "chat" && (
        <div className="p-4 md:p-6 bg-zinc-950 border-t border-zinc-900">
          <div className="max-w-3xl mx-auto relative flex gap-3">
            <Button 
              size="icon" 
              className={`h-14 w-14 rounded-full transition-all ${isListening ? 'bg-red-500 animate-pulse' : 'bg-zinc-800 hover:bg-zinc-700'}`}
              onClick={toggleListening}
            >
              <Mic className="h-6 w-6 text-white" />
            </Button>
            
            <Input 
              className="h-14 bg-zinc-900 border-zinc-800 text-lg px-6 rounded-full focus-visible:ring-emerald-500"
              placeholder="Ask me anything... (e.g. 'Where is the red dress?')"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
            />
            
            <Button 
              size="icon" 
              className="h-14 w-14 rounded-full bg-white hover:bg-zinc-200 text-black"
              onClick={() => handleSend()}
            >
              <Send className="h-6 w-6" />
            </Button>
          </div>
          <p className="text-center text-zinc-500 text-xs mt-3">Tap microphone to speak or type your question.</p>
        </div>
      )}
    </div>
  );
}