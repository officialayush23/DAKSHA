import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Carousel } from 'antd'; 
import { Send, ShoppingBag, MapPin, Sparkles, User, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
// 👇 FIXED: Added SessionService import
import api, { SessionService } from '../lib/api'; 
import { toast } from 'sonner';

const { Meta } = Card;

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: "Welcome back. I am your Daksha Concierge. How may I assist your style journey today?",
      current_agent: "AI Concierge" 
    }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("AI Concierge");
  
  // 👇 FIXED: Added state to hold the session_id
  const [sessionId, setSessionId] = useState(null);
  const scrollRef = useRef(null);

  // 👇 FIXED: Fetch the active session when the chat component mounts
  useEffect(() => {
    const fetchSession = async () => {
      try {
        const res = await SessionService.getActive();
        const data = res?.data || res;
        if (data?.session_id) {
          setSessionId(data.session_id);
        }
      } catch (err) {
        console.error("Failed to load session", err);
      }
    };
    fetchSession();
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const onAction = async (text) => {
    if (!text.trim()) return;
    
    if (!sessionId) {
      toast.error("Waiting for secure session to initialize...");
      return;
    }

    // Add User Message
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      // 👇 FIXED: Passed session_id in the body exactly as the backend requested!
      const res = await api.post('/chat/', { 
        message: text,
        session_id: sessionId
      });
      
      const data = res.data || res;
      
      if (data.current_agent) {
        setCurrentAgent(data.current_agent);
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || "I didn't quite catch that.",
        products: data.ui_elements?.products || [],
        actions: data.ui_elements?.actions || []
      }]);

    } catch (err) {
      console.error("Agent Error:", err);
      
      if (err.response && err.response.status === 422) {
        console.error("🚨 SCHEMA MISMATCH DETAILS 🚨:", JSON.stringify(err.response.data.detail, null, 2));
        toast.error("Format Error: Check browser console for exact backend requirements.");
      } else {
        toast.error("Connection lost. Please try again.");
      }

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I apologize, I'm experiencing a brief interruption in my service." 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto bg-white rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.05)] overflow-hidden border border-zinc-100">
      
      {/* --- HEADER --- */}
      <div className="px-8 py-6 bg-zinc-900 text-white flex justify-between items-center shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-zinc-700 to-zinc-800 flex items-center justify-center border border-zinc-600">
            <Sparkles size={22} className="text-zinc-200" />
          </div>
          <div>
            <h2 className="font-serif text-2xl tracking-tight">Daksha Agent</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-400 font-bold">
                Active: <span className="text-emerald-400">{currentAgent}</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* --- CHAT HISTORY --- */}
      <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 scrollbar-hide">
        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex gap-4 max-w-[80%] ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar Icons */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border ${
                  m.role === 'user' ? 'bg-zinc-100 border-zinc-200' : 'bg-black border-black text-white'
                }`}>
                  {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>

                <div className={`space-y-4 ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                  {/* Message Bubble */}
                  <div className={`p-5 rounded-2xl text-[15px] leading-relaxed shadow-sm transition-all ${
                    m.role === 'user' 
                      ? 'bg-zinc-900 text-white rounded-tr-none' 
                      : 'bg-[#F9F9F9] text-zinc-800 border border-zinc-100 rounded-tl-none'
                  }`}>
                    {m.content}
                  </div>

                  {/* Optional Product Carousel */}
                  {m.products?.length > 0 && (
                    <div className="w-[280px] md:w-[480px] py-2">
                      <Carousel dots={false} arrows infinite={false} slidesToShow={window.innerWidth > 768 ? 2 : 1}>
                        {m.products.map((p, idx) => (
                          <div key={idx} className="px-2">
                            <Card
                              hoverable
                              className="rounded-2xl border-zinc-100 overflow-hidden shadow-sm"
                              cover={<img src={p.image} className="h-40 object-cover bg-zinc-50" />}
                              actions={[
                                <ShoppingBag key="add" size={16} onClick={() => onAction(`Add ${p.name} to bag`)} />,
                                <MapPin key="info" size={16} />
                              ]}
                            >
                              <Meta title={<span className="font-bold text-sm">{p.name}</span>} description={`₹${p.price}`} />
                            </Card>
                          </div>
                        ))}
                      </Carousel>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing State */}
        {isTyping && (
          <div className="flex gap-4 items-center pl-12">
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 bg-zinc-300 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 bg-zinc-300 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 bg-zinc-300 rounded-full animate-bounce" />
            </div>
            <span className="text-[10px] uppercase tracking-widest text-zinc-400 font-bold italic">
              {currentAgent} is processing...
            </span>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* --- INPUT AREA --- */}
      <div className="p-8 bg-white border-t border-zinc-100 shrink-0">
        <div className="max-w-4xl mx-auto relative flex items-center gap-4">
          <input 
            className="flex-1 bg-zinc-50 border border-zinc-200 rounded-2xl px-6 py-5 outline-none font-sans text-sm focus:ring-2 focus:ring-black/5 focus:border-black transition-all"
            placeholder="Type your request (e.g., 'Track my return' or 'Suggest a summer outfit')..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onAction(input)}
            disabled={isTyping}
          />
          <button 
            onClick={() => onAction(input)}
            disabled={!input.trim() || isTyping}
            className="w-14 h-14 bg-black rounded-2xl flex items-center justify-center text-white hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:grayscale"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}