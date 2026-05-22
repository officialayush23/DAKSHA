import React, { useState, useEffect, useRef } from 'react';
import { Card } from 'antd';
import { Send, ShoppingBag, Sparkles, User, Bot, Mic, MicOff, Plus, MessageSquare, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import api from '../lib/api';
import { toast } from 'sonner';

// ── Recommendation outcome tracker ──────────────────────────────────────────
const logRecommendationOutcome = async (impressionId, outcomeType, rewardValue = 0.1) => {
  if (!impressionId) return;
  try {
    await api.post('/recommendations/outcome', {
      impression_id: impressionId,
      outcome_type: outcomeType,
      reward_value: rewardValue,
    });
  } catch (_) {
    // Fire-and-forget — never surface errors to user
  }
};

const { Meta } = Card;

const WELCOME_MSG = {
  role: 'assistant',
  content: "Welcome back. I am your Daksha Concierge. How may I assist your style journey today?",
  current_agent: "Unified Agent"
};

export default function ChatInterface() {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // session_id lives in the URL (?sid=...) so it survives page refresh
  const sidFromUrl = searchParams.get("sid");
  const sidFromState = location.state?.sessionId ?? null;

  // On first render, if navigated with router state, promote it into the URL
  const [sessionId, setSessionId] = useState(sidFromUrl || sidFromState);

  const [messages, setMessages] = useState([WELCOME_MSG]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("Unified Agent");
  const scrollRef = useRef(null);

  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  // Web Speech API mic handler
  const toggleMic = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      toast.error('Speech recognition not supported in this browser.');
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setInput(prev => (prev ? prev + ' ' + transcript : transcript));
      setIsListening(false);
    };
    recognition.onerror = () => { setIsListening(false); toast.error('Mic error — try again'); };
    recognition.onend  = () => setIsListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
  };


  // Sync router state → URL param (once, on navigate-with-state)
  useEffect(() => {
    if (sidFromState && sidFromState !== sidFromUrl) {
      setSearchParams({ sid: sidFromState }, { replace: true });
      setSessionId(sidFromState);
    }
  }, [sidFromState]);

  // Load message history whenever sessionId changes to a real value
  useEffect(() => {
    if (!sessionId) {
      setMessages([WELCOME_MSG]);
      return;
    }
    const load = async () => {
      setLoadingHistory(true);
      try {
        const res = await api.get(`/chat/sessions/${sessionId}/messages`);
        const history = res.data || [];
        if (history.length > 0) {
          setMessages(history.map(m => ({
            role: m.role,
            content: m.content,
            // Restore product cards from persisted ui_data
            products: m.ui_data
              ? (m.ui_data.products || m.ui_data.trending_products || m.ui_data.items || [])
              : [],
          })));
        } else {
          setMessages([WELCOME_MSG]);
        }
      } catch {
        setMessages([WELCOME_MSG]);
      } finally {
        setLoadingHistory(false);
      }
    };
    load();
  }, [sessionId]);

  // Auto-scroll to latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const onAction = async (text) => {
    if (!text.trim()) return;

    // Add User Message
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const res = await api.post('/chat/', {
        message: text,
        session_id: sessionId   // null on first message → backend creates new session
      });

      const data = res.data || res;

      // Capture the session_id returned by backend (important on first message)
      // Also write it to the URL so the conversation survives a page refresh
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        setSearchParams({ sid: data.session_id }, { replace: true });
      }

      if (data.current_agent) {
        setCurrentAgent(data.current_agent);
      }

      const uiData = data.ui_data || {};
      const productsList = uiData.products || uiData.trending_products || uiData.items || [];

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || "I have processed your request.",
        products: productsList
      }]);

    } catch (err) {
      console.error("Agent Error:", err);
      toast.error("Connection lost. Please try again.");
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I apologize, I'm experiencing a brief interruption in my service."
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const startNewChat = () => {
    setSessionId(null);
    setMessages([WELCOME_MSG]);
    setCurrentAgent("Unified Agent");
    setInput("");
    // Clear URL param so a fresh session is created on the next message
    navigate('/dash/agent', { replace: true, state: {} });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto bg-white rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.05)] overflow-hidden border border-zinc-100">
      
      {/* --- HEADER --- */}
      <div className="px-6 py-5 bg-zinc-900 text-white flex justify-between items-center shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-zinc-700 to-zinc-800 flex items-center justify-center border border-zinc-600">
            <Sparkles size={20} className="text-zinc-200" />
          </div>
          <div>
            <h2 className="font-serif text-xl tracking-tight">Daksha Agent</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-400 font-bold">
                Active: <span className="text-emerald-400">{currentAgent}</span>
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/dash/chats')}
            title="View all conversations"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white text-[11px] uppercase tracking-widest transition-all"
          >
            <MessageSquare size={13} />
            <span className="hidden sm:inline">History</span>
          </button>
          <button
            onClick={startNewChat}
            title="Start a new conversation"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white text-[11px] uppercase tracking-widest transition-all"
          >
            <Plus size={13} />
            <span className="hidden sm:inline">New Chat</span>
          </button>
        </div>
      </div>

      {/* --- CHAT HISTORY --- */}
      <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 scrollbar-hide relative">
        {loadingHistory && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/70 z-10">
            <Loader2 size={28} className="animate-spin text-zinc-400" />
          </div>
        )}
        <AnimatePresence initial={false}>
          {messages.map((m, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex gap-4 max-w-[90%] md:max-w-[80%] ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                
                {/* Avatar Icons */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border ${
                  m.role === 'user' ? 'bg-zinc-100 border-zinc-200' : 'bg-black border-black text-white'
                }`}>
                  {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>

                <div className={`space-y-4 ${m.role === 'user' ? 'items-end' : 'items-start'} overflow-hidden`}>
                  
                  {/* Message Bubble */}
                  <div className={`p-5 rounded-2xl text-[15px] leading-relaxed shadow-sm transition-all inline-block ${
                    m.role === 'user' 
                      ? 'bg-zinc-900 text-white rounded-tr-none' 
                      : 'bg-[#F9F9F9] text-zinc-800 border border-zinc-100 rounded-tl-none'
                  }`}>
                    {m.content}
                  </div>

                  {/* 👇 HORIZONTAL INFINITE SCROLL GRID FOR PRODUCTS 👇 */}
                  {m.products?.length > 0 && (
                    <div className="flex overflow-x-auto gap-4 pb-4 pt-2 snap-x scrollbar-hide w-full max-w-[300px] sm:max-w-[450px] md:max-w-[600px]">
                      {m.products.map((p, idx) => (
                        <div key={idx} className="snap-start shrink-0 w-[200px]">
                          <Card
                            hoverable
                            className="rounded-2xl border-zinc-200 overflow-hidden shadow-sm hover:shadow-md transition-all h-full flex flex-col"
                            bodyStyle={{ padding: '12px' }}
                            onClick={() => logRecommendationOutcome(p.impression_id, 'click', 0.1)}
                            cover={
                              <div className="h-40 w-full bg-zinc-100 overflow-hidden">
                                <img 
                                  // Defensively handle different image key names from backend
                                  src={p.image || p.image_url || "https://via.placeholder.com/200"} 
                                  alt={p.name}
                                  className="w-full h-full object-cover" 
                                />
                              </div>
                            }
                            actions={[
                              <ShoppingBag
                                key="add"
                                size={18}
                                className="text-zinc-600 hover:text-black transition-colors"
                                onClick={() => {
                                  logRecommendationOutcome(p.impression_id, 'cart', 0.5);
                                  onAction(`Add ${p.name} to my cart`);
                                }}
                              />
                            ]}
                          >
                            <Meta 
                              title={<span className="font-bold text-sm whitespace-normal line-clamp-2 leading-tight">{p.name}</span>} 
                              description={
                                <div className="mt-2 text-black font-semibold">
                                  {/* Handle price or final_price keys */}
                                  ₹{p.final_price || p.price || p.base_price || 0}
                                </div>
                              } 
                            />
                          </Card>
                        </div>
                      ))}
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
          </div>
        )}
        <div ref={scrollRef} />
      </div> {/* end chat history */}

      {/* --- INPUT AREA --- */}
      <div className="p-6 md:p-8 bg-white border-t border-zinc-100 shrink-0">
        <div className="max-w-4xl mx-auto relative flex items-center gap-4">
          <input 
            className="flex-1 bg-zinc-50 border border-zinc-200 rounded-2xl px-6 py-4 outline-none font-sans text-sm focus:ring-2 focus:ring-black/5 focus:border-black transition-all"
            placeholder={isListening ? "Listening…" : "Type or speak your request…"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onAction(input)}
            disabled={isTyping}
          />
          {/* Mic button */}
          <button
            onClick={toggleMic}
            disabled={isTyping}
            title={isListening ? 'Stop listening' : 'Speak'}
            className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all disabled:opacity-30 ${
              isListening
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
            }`}
          >
            {isListening ? <MicOff size={20} /> : <Mic size={20} />}
          </button>
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