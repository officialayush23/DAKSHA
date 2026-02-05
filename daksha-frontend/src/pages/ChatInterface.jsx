import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Carousel, Typography, Space } from 'antd'; // AntD for rich components
import { Send, ShoppingBag, MapPin, RefreshCcw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../lib/api';

const { Meta } = Card;

export default function ChatInterface({ channel = 'web' }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onAction = async (text) => {
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const { data } = await api.post('/chat/message', { message: text, channel });
      
      // Handle the complex response object
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply,
        products: data.ui_elements?.products || [],
        actions: data.ui_elements?.actions || []
      }]);
    } catch (err) {
      console.error("Agent disconnect", err);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[85vh] max-w-4xl mx-auto bg-daksha-cream rounded-3xl shadow-2xl overflow-hidden border border-zinc-100">
      {/* Header */}
      <div className="p-6 bg-daksha-black text-white flex justify-between items-center">
        <h2 className="font-serif text-3xl tracking-tighter">DAKSHA Agent</h2>
        <div className="flex gap-2">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-[10px] uppercase tracking-widest opacity-60">Identity Synced</span>
        </div>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8 scroll-smooth">
        {messages.map((m, i) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={i} 
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className="max-w-[85%] space-y-4">
              {/* Message Bubble */}
              <div className={`p-5 rounded-2xl text-sm leading-relaxed shadow-sm ${
                m.role === 'user' ? 'bg-daksha-black text-white' : 'bg-white text-zinc-800'
              }`}>
                {m.content}
              </div>

              {/* PRODUCT CAROUSEL (Conditional Rendering) */}
              {m.products?.length > 0 && (
                <div className="w-[320px] md:w-[450px]">
                  <Carousel dots={false} arrows infinite={false} slidesToShow={window.innerWidth > 768 ? 2 : 1}>
                    {m.products.map(p => (
                      <div key={p.variant_id} className="px-2">
                        <Card
                          hoverable
                          className="border-none shadow-md overflow-hidden rounded-xl"
                          cover={<img src={p.image} className="bw-image h-48 object-cover" alt={p.brand} />}
                          actions={[
                            <ShoppingBag key="add" size={16} onClick={() => onAction(`Add ${p.brand} ${p.category} to my bag`)} />,
                            <MapPin key="locate" size={16} onClick={() => onAction(`Check local stock for this`)} />
                          ]}
                        >
                          <Meta title={<span className="font-serif italic">{p.brand}</span>} description={`₹${p.price}`} />
                        </Card>
                      </div>
                    ))}
                  </Carousel>
                </div>
              )}

              {/* QUICK ACTION BUTTONS */}
              {m.actions?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {m.actions.map(act => (
                    <Button 
                      key={act.label} 
                      className="rounded-full border-daksha-black text-daksha-black hover:bg-daksha-black hover:text-white text-xs uppercase tracking-widest h-9"
                      onClick={() => onAction(act.label)}
                    >
                      {act.label}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ))}
        {isTyping && <div className="text-xs italic text-zinc-400 animate-pulse font-serif">Daksha is thinking...</div>}
        <div ref={scrollRef} />
      </div>

      {/* Input */}
      <div className="p-6 bg-white border-t border-zinc-100 flex gap-4 items-center">
        <input 
          className="flex-1 bg-zinc-50 border-none rounded-full px-6 py-4 outline-none font-sans text-sm focus:ring-1 ring-zinc-200"
          placeholder="Ask for style recommendations or track orders..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onAction(input)}
        />
        <button 
          onClick={() => onAction(input)}
          className="w-12 h-12 bg-daksha-black rounded-full flex items-center justify-center text-white hover:bg-daksha-accent transition-all"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}