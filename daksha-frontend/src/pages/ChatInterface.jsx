import React, { useState, useEffect, useRef } from 'react';
import { Card } from 'antd';
import {
  Send, ShoppingBag, Sparkles, User, Bot, Mic, MicOff,
  Plus, MessageSquare, Loader2, ImagePlus, X,
  CheckCircle2, AlertCircle, RefreshCw,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useBasePath } from '../hooks/useBasePath';
import api from '../lib/api';
import { toast } from 'sonner';
// Image uploads go through the backend (/chat/upload-image) to bypass Supabase RLS

// ── Recommendation outcome tracker ──────────────────────────────────────────
const logRecommendationOutcome = async (impressionId, outcomeType, rewardValue = 0.1) => {
  if (!impressionId) return;
  try {
    await api.post('/recommendations/outcome', {
      impression_id: impressionId,
      outcome_type: outcomeType,
      reward_value: rewardValue,
    });
  } catch (_) {}
};

// ── Direct cart add (no AI needed) ──────────────────────────────────────────
const directAddToCart = async (variantId, impressionId, productName, toastFn) => {
  logRecommendationOutcome(impressionId, 'cart', 0.5);
  try {
    await api.post('/cart/quick-add', { variant_id: variantId, quantity: 1 });
    toastFn?.success('Added to cart!');
  } catch (err) {
    const detail = err?.response?.data?.detail || 'Could not add to cart';
    toastFn?.error(detail);
  }
};

const { Meta } = Card;

const WELCOME_MSG = {
  role: 'assistant',
  content: 'Welcome back. I am your Daksha Concierge. How may I assist your style journey today?',
  current_agent: 'Unified Agent',
};

export default function ChatInterface() {
  const location = useLocation();
  const navigate = useNavigate();
  const { basePath } = useBasePath();
  const [searchParams, setSearchParams] = useSearchParams();

  const sidFromUrl   = searchParams.get('sid');
  const sidFromState = location.state?.sessionId ?? null;

  const [sessionId,     setSessionId]     = useState(sidFromUrl || sidFromState);
  const [messages,      setMessages]      = useState([WELCOME_MSG]);
  const [loadingHistory,setLoadingHistory] = useState(false);
  const [input,         setInput]         = useState('');
  const [isTyping,      setIsTyping]      = useState(false);
  const [currentAgent,  setCurrentAgent]  = useState('Unified Agent');
  const scrollRef = useRef(null);

  const [isListening,   setIsListening]   = useState(false);
  const recognitionRef = useRef(null);

  // ── Image upload state ───────────────────────────────────────────────────
  // { preview: blobURL, url: supabaseURL|null, status: 'uploading'|'ready'|'error', file: File }
  const [pendingImage, setPendingImage] = useState(null);
  const fileInputRef = useRef(null);

  const _doUpload = async (file, preview) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/chat/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const publicUrl = res.data?.url || res.url;
      if (!publicUrl) throw new Error('No URL returned from server');
      setPendingImage({ preview, url: publicUrl, status: 'ready', file });
      toast.success('Image ready to send!');
    } catch (err) {
      console.error('[IMAGE UPLOAD]', err);
      setPendingImage({ preview, url: null, status: 'error', file });
      toast.error('Upload failed — tap ↺ to retry');
    }
  };

  const handleImageSelect = async (e) => {
    const file = e.target.files?.[0];
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (!file) return;
    if (!file.type.startsWith('image/')) { toast.error('Please select an image file.'); return; }
    if (file.size > 10 * 1024 * 1024) { toast.error('Image must be under 10 MB.'); return; }

    const preview = URL.createObjectURL(file);
    setPendingImage({ preview, url: null, status: 'uploading', file });
    await _doUpload(file, preview);
  };

  const retryUpload = async () => {
    if (!pendingImage?.file || !pendingImage?.preview) return;
    setPendingImage(prev => ({ ...prev, status: 'uploading' }));
    await _doUpload(pendingImage.file, pendingImage.preview);
  };

  const clearPendingImage = () => {
    if (pendingImage?.preview) URL.revokeObjectURL(pendingImage.preview);
    setPendingImage(null);
  };

  // ── Web Speech API ───────────────────────────────────────────────────────
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
    recognition.onend   = () => setIsListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
  };

  // ── Sync router state → URL param ────────────────────────────────────────
  useEffect(() => {
    if (sidFromState && sidFromState !== sidFromUrl) {
      setSearchParams({ sid: sidFromState }, { replace: true });
      setSessionId(sidFromState);
    }
  }, [sidFromState]);

  // ── Load message history when sessionId changes ───────────────────────────
  useEffect(() => {
    if (!sessionId) { setMessages([WELCOME_MSG]); return; }
    const load = async () => {
      setLoadingHistory(true);
      try {
        const res = await api.get(`/chat/sessions/${sessionId}/messages`);
        const history = res.data || [];
        if (history.length > 0) {
          setMessages(history.map(m => ({
            role: m.role,
            content: m.content,
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

  // ── Auto-scroll ───────────────────────────────────────────────────────────
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // ── Send message ──────────────────────────────────────────────────────────
  const onAction = async (text) => {
    if (pendingImage?.status === 'uploading') {
      toast.error('Please wait — image is still uploading…');
      return;
    }

    const imageUrl   = pendingImage?.status === 'ready' ? (pendingImage.url || null) : null;
    const imgPreview = pendingImage?.preview || null;
    const messageText = text.trim() || (imageUrl ? 'Find me products similar to this image.' : '');
    if (!messageText) return;

    const capturedPreview = imgPreview;
    const userMsg = { role: 'user', content: messageText, image_url: imageUrl, image_preview: capturedPreview };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setPendingImage(null);
    if (capturedPreview) setTimeout(() => URL.revokeObjectURL(capturedPreview), 8000);
    setIsTyping(true);

    try {
      const res  = await api.post('/chat/', { message: messageText, session_id: sessionId, image_url: imageUrl });
      const data = res.data || res;

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        setSearchParams({ sid: data.session_id }, { replace: true });
      }
      if (data.current_agent) setCurrentAgent(data.current_agent);

      const uiData = data.ui_data || {};
      const productsList = uiData.products || uiData.trending_products || uiData.items || [];

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || 'I have processed your request.',
        products: productsList,
      }]);
    } catch (err) {
      console.error('Agent Error:', err);
      toast.error('Connection lost. Please try again.');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'I apologize, I\'m experiencing a brief interruption in my service.',
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const startNewChat = () => {
    setSessionId(null);
    setMessages([WELCOME_MSG]);
    setCurrentAgent('Unified Agent');
    setInput('');
    navigate(`${basePath}/agent`, { replace: true, state: {} });
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto bg-white rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.05)] overflow-hidden border border-zinc-100">

      {/* HEADER */}
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
            onClick={() => navigate(`${basePath}/chats`)}
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

      {/* CHAT HISTORY */}
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

                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border ${
                  m.role === 'user' ? 'bg-zinc-100 border-zinc-200' : 'bg-black border-black text-white'
                }`}>
                  {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>

                <div className={`space-y-3 ${m.role === 'user' ? 'items-end' : 'items-start'} overflow-hidden flex flex-col`}>

                  {/* Attached image — user messages only */}
                  {(m.image_preview || m.image_url) && m.role === 'user' && (
                    <div className="rounded-2xl overflow-hidden border border-zinc-700 shadow-md max-w-[260px] bg-zinc-800 self-end">
                      <img
                        src={m.image_preview || m.image_url}
                        alt="Attached image"
                        className="w-full max-h-[300px] object-cover block"
                        onError={(e) => {
                          if (m.image_url && e.target.src !== m.image_url) {
                            e.target.src = m.image_url;
                          }
                        }}
                      />
                      <div className="px-3 py-1.5 flex items-center gap-1.5">
                        <ImagePlus size={11} className="text-zinc-400" />
                        <span className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider">Image search</span>
                      </div>
                    </div>
                  )}

                  {/* Text bubble */}
                  <div className={`p-5 rounded-2xl text-[15px] leading-relaxed shadow-sm transition-all inline-block ${
                    m.role === 'user'
                      ? 'bg-zinc-900 text-white rounded-tr-none self-end'
                      : 'bg-[#F9F9F9] text-zinc-800 border border-zinc-100 rounded-tl-none'
                  }`}>
                    {m.content}
                  </div>

                  {/* Product cards */}
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
                                  src={p.image || p.image_url || 'https://via.placeholder.com/200'}
                                  alt={p.name}
                                  className="w-full h-full object-cover"
                                />
                              </div>
                            }
                            actions={[
                              <ShoppingBag
                                key="add"
                                size={18}
                                className="text-zinc-600 hover:text-black transition-colors cursor-pointer"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  directAddToCart(p.variant_id, p.impression_id, p.name, toast);
                                }}
                              />,
                            ]}
                          >
                            <Meta
                              title={<span className="font-bold text-sm whitespace-normal line-clamp-2 leading-tight">{p.name}</span>}
                              description={
                                <div className="mt-1 space-y-0.5">
                                  {(p.color || p.size) && (
                                    <div className="text-xs text-zinc-500">
                                      {[p.color, p.size].filter(Boolean).join(' · ')}
                                    </div>
                                  )}
                                  <div className="text-black font-semibold text-sm">
                                    ₹{p.final_price || p.price || p.base_price || 0}
                                  </div>
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

        {/* Typing indicator */}
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
      </div>

      {/* INPUT AREA */}
      <div className="p-6 md:p-8 bg-white border-t border-zinc-100 shrink-0">
        <div className="max-w-4xl mx-auto space-y-3">

          {/* Image attachment preview strip */}
          <AnimatePresence>
            {pendingImage && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-center gap-4 px-1 overflow-hidden"
              >
                {/* Thumbnail */}
                <div className={`relative w-[72px] h-[72px] rounded-xl overflow-hidden shrink-0 border-2 transition-colors ${
                  pendingImage.status === 'error'   ? 'border-red-400'
                  : pendingImage.status === 'ready' ? 'border-emerald-400'
                  : 'border-zinc-300'
                }`}>
                  <img src={pendingImage.preview} alt="Attachment preview" className="w-full h-full object-cover" />

                  {pendingImage.status === 'uploading' && (
                    <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center gap-1">
                      <Loader2 size={18} className="animate-spin text-white" />
                      <span className="text-[9px] text-white/80 font-bold uppercase tracking-wider">Uploading</span>
                    </div>
                  )}

                  {pendingImage.status === 'ready' && (
                    <div className="absolute bottom-1 right-1 bg-emerald-500 rounded-full p-0.5 shadow">
                      <CheckCircle2 size={12} className="text-white" />
                    </div>
                  )}

                  {pendingImage.status === 'error' && (
                    <div className="absolute inset-0 bg-red-900/50 flex items-center justify-center">
                      <AlertCircle size={22} className="text-red-300" />
                    </div>
                  )}

                  {pendingImage.status !== 'uploading' && (
                    <button
                      onClick={clearPendingImage}
                      className="absolute top-1 left-1 w-5 h-5 bg-zinc-900/70 rounded-full flex items-center justify-center text-white hover:bg-red-500 transition-colors"
                    >
                      <X size={9} />
                    </button>
                  )}
                </div>

                {/* Status text */}
                <div className="flex-1 min-w-0">
                  {pendingImage.status === 'uploading' && (
                    <p className="text-sm text-zinc-500 font-medium">Uploading image…</p>
                  )}
                  {pendingImage.status === 'ready' && (
                    <>
                      <p className="text-sm text-emerald-700 font-semibold flex items-center gap-1.5">
                        <CheckCircle2 size={13} /> Image attached
                      </p>
                      <p className="text-xs text-zinc-400 mt-0.5">Add a message or hit send to find similar products</p>
                    </>
                  )}
                  {pendingImage.status === 'error' && (
                    <>
                      <p className="text-sm text-red-600 font-semibold flex items-center gap-1.5">
                        <AlertCircle size={13} /> Upload failed
                      </p>
                      <button
                        onClick={retryUpload}
                        className="mt-1 flex items-center gap-1 text-xs text-zinc-600 hover:text-black font-medium underline underline-offset-2"
                      >
                        <RefreshCw size={11} /> Retry upload
                      </button>
                    </>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Text input row */}
          <div className="relative flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleImageSelect}
            />

            {/* Image attach button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isTyping || pendingImage?.status === 'uploading'}
              title="Attach image for visual search"
              className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all shrink-0 disabled:opacity-30 ${
                pendingImage?.status === 'ready'
                  ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                  : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              <ImagePlus size={18} />
            </button>

            <input
              className="flex-1 bg-zinc-50 border border-zinc-200 rounded-2xl px-6 py-4 outline-none font-sans text-sm focus:ring-2 focus:ring-black/5 focus:border-black transition-all"
              placeholder={
                isListening                            ? 'Listening…'
                : pendingImage?.status === 'uploading' ? 'Uploading image, one moment…'
                : pendingImage?.status === 'ready'     ? 'Describe what you\'re looking for (or just hit send)…'
                : 'Type or speak your request…'
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && onAction(input)}
              disabled={isTyping}
            />

            {/* Mic */}
            <button
              onClick={toggleMic}
              disabled={isTyping}
              title={isListening ? 'Stop listening' : 'Speak'}
              className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all disabled:opacity-30 shrink-0 ${
                isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              {isListening ? <MicOff size={18} /> : <Mic size={18} />}
            </button>

            {/* Send */}
            <button
              onClick={() => onAction(input)}
              disabled={
                isTyping ||
                pendingImage?.status === 'uploading' ||
                (!input.trim() && pendingImage?.status !== 'ready')
              }
              className="w-12 h-12 bg-black rounded-2xl flex items-center justify-center text-white hover:scale-105 active:scale-95 transition-all disabled:opacity-30 disabled:grayscale shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
