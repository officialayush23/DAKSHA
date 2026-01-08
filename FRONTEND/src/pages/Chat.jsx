// src/pages/Chat.jsx
import React, { useEffect, useRef, useState } from "react";
import api from "@/lib/apiClient";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Sparkles, Mic, MicOff, Volume2, VolumeX, Code, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
// Collapsible will be imported if available, otherwise use simple toggle
import { getSessionId } from "@/lib/analytics";
import ChatProductCard from "@/components/chat/ChatProductCard";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

// --- SPEECH UTILS ---
const synth = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

// JSON Viewer Component
function JSONViewer({ data, title = "Payload" }) {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!data) return null;
  
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mt-2">
      <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full">
        {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        <Code className="h-3 w-3" />
        <span>{title}</span>
        <Badge variant="outline" className="text-[10px] px-1.5 py-0 ml-auto">
          {typeof data === 'object' ? 'JSON' : 'Text'}
        </Badge>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <pre className="text-xs bg-muted/50 p-3 rounded-md overflow-auto max-h-64 font-mono border border-border/40 mt-2">
          {JSON.stringify(data, null, 2)}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  );
}

// Message bubble component
function Message({ msg }) {
  const isUser = msg.role === "user";

  const renderContent = () => {
    const content = msg.content;
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) return content.map(c => c.text || "").join("\n");
    if (typeof content === 'object' && content !== null) {
       return content.reply || content.text || content.message || JSON.stringify(content);
    }
    return String(content);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`flex flex-col max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        
        <div
          className={`px-4 py-3 text-sm leading-relaxed rounded-xl
          ${
            isUser
              ? "bg-primary text-primary-foreground rounded-br-none"
              : "bg-card border border-border/40 rounded-tl-none"
          }`}
        >
          {!isUser && (
            <div className="flex items-center gap-2 mb-1 text-xs text-muted-foreground">
              <Bot className="h-3.5 w-3.5" />
              Daksha
              {msg.confidence !== undefined && (
                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                  {Math.round(msg.confidence * 100)}%
                </Badge>
              )}
            </div>
          )}
          <div className="whitespace-pre-wrap">{renderContent()}</div>
        </div>

        {/* 🛍️ PRODUCT CAROUSEL */}
        {msg.payload?.type === 'products' && msg.payload.data?.length > 0 && (
          <div className="mt-2 w-full flex gap-2 overflow-x-auto pb-2 pt-1 scrollbar-hide snap-x">
            {msg.payload.data.map(p => (
              <div key={p.id || p.product_variant_id} className="snap-start shrink-0">
                <ChatProductCard product={p} />
              </div>
            ))}
          </div>
        )}

        {/* 📦 ORDER HISTORY */}
        {msg.payload?.type === 'order_history' && msg.payload.data && (
          <div className="mt-2 p-3 bg-muted/50 rounded-lg border border-border/40 text-sm w-full max-w-xs">
            <div className="font-semibold mb-2">Order History</div>
            {Array.isArray(msg.payload.data) ? (
              <div className="space-y-2">
                {msg.payload.data.slice(0, 3).map((order, idx) => (
                  <div key={idx} className="text-xs p-2 bg-background rounded border">
                    <div className="font-medium">Order #{order.id?.slice(0, 8)}</div>
                    <div className="text-muted-foreground">₹{order.total_amount} • {order.status}</div>
                  </div>
                ))}
                {msg.payload.data.length > 3 && (
                  <div className="text-xs text-muted-foreground">+{msg.payload.data.length - 3} more</div>
                )}
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">{JSON.stringify(msg.payload.data)}</div>
            )}
          </div>
        )}

        {/* 🎯 RECOMMENDATIONS */}
        {msg.payload?.type === 'recommendations' && msg.payload.data && (
          <div className="mt-2 p-3 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-950/20 dark:to-indigo-950/20 rounded-lg border border-purple-200/50 dark:border-purple-800/50 text-sm w-full max-w-xs">
            <div className="font-semibold mb-2 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-600" />
              Recommendations
            </div>
            {Array.isArray(msg.payload.data) && msg.payload.data.length > 0 ? (
              <div className="space-y-2">
                {msg.payload.data.slice(0, 3).map((rec, idx) => (
                  <div key={idx} className="text-xs p-2 bg-background rounded border">
                    {rec.name || rec.product_name || `Item ${idx + 1}`}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-muted-foreground">No recommendations available</div>
            )}
          </div>
        )}

        {/* 🛒 CART SUMMARY */}
        {msg.payload?.type === 'cart' && msg.payload.data && (
          <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200/50 dark:border-blue-800/50 text-sm w-full max-w-xs">
            <div className="font-semibold mb-2">Cart</div>
            <div className="text-xs">
              {msg.payload.data.item_count || msg.payload.data.items?.length || 0} items
              {msg.payload.data.total && ` • ₹${msg.payload.data.total}`}
            </div>
          </div>
        )}

        {/* 🔍 JSON VIEWER (Debug) */}
        {msg.payload && (
          <JSONViewer data={msg.payload} title="Agent Payload" />
        )}

        {/* ⚠️ LOW CONFIDENCE WARNING */}
        {msg.confidence !== undefined && msg.confidence < 0.4 && (
          <div className="mt-2 flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
            <AlertCircle className="h-3 w-3" />
            <span>Low confidence - escalated to human agent</span>
          </div>
        )}

      </div>
    </motion.div>
  );
}

// Chat Page Main Logic
export default function Chat() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(true); 
  const recognitionRef = useRef(null);
  const scrollRef = useRef(null);
  const wsRef = useRef(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!conversationId) return;

    const wsUrl = (import.meta.env.VITE_BACKEND_BASE_URL || "http://localhost:8000")
      .replace("http://", "ws://")
      .replace("https://", "wss://");
    
    const ws = new WebSocket(`${wsUrl}/ws/chat/${conversationId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("✅ Chat WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Add new message from WebSocket
        if (data.sender && data.content) {
          setMessages(prev => [...prev, {
            id: data.id || crypto.randomUUID(),
            role: data.sender === "user" ? "user" : "assistant",
            content: data.content,
            payload: data.metadata,
            confidence: data.confidence
          }]);
        }
      } catch (e) {
        console.error("WS message parse error:", e);
      }
    };

    ws.onerror = (e) => {
      console.warn("WS Error:", e);
    };

    ws.onclose = () => {
      console.log("🔕 Chat WebSocket disconnected");
    };

    return () => {
      ws.close();
    };
  }, [conversationId]);

  useEffect(() => {
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.lang = "en-IN";
      recognition.interimResults = false;
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        sendMessage(transcript); 
      };
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

  // 🔊 SAFE SPEAK FUNCTION
  const speak = (text) => {
    if (!isSpeaking || !synth) return;
    
    let safeText = "";
    if (typeof text === 'string') safeText = text;
    else if (typeof text === 'object' && text !== null) safeText = text.reply || text.text || "I found something for you.";
    else safeText = String(text);

    synth.cancel(); 
    const utterance = new SpeechSynthesisUtterance(safeText);
    synth.speak(utterance);
  };

  const toggleMic = () => {
    if (!recognitionRef.current) return alert("Browser does not support Speech API");
    if (isListening) recognitionRef.current.stop();
    else {
        recognitionRef.current.start();
        setIsListening(true);
    }
  };

  // Load conversation history on mount
  useEffect(() => {
    const loadHistory = async () => {
      if (!user) {
        setMessages([{
          id: "welcome",
          role: "assistant",
          content: "Hi 👋 I'm Daksha. How can I help you shop today?",
        }]);
        return;
      }

      try {
        // Get recent conversations
        const convsRes = await api.get("/channels/conversations?limit=1");
        if (convsRes.data.conversations && convsRes.data.conversations.length > 0) {
          const latestConv = convsRes.data.conversations[0];
          setConversationId(latestConv.id);
          
          // Load messages for this conversation
          const msgsRes = await api.get(`/channels/conversations/${latestConv.id}/messages?limit=20`);
          if (msgsRes.data.messages) {
            const formatted = msgsRes.data.messages.map(m => ({
              id: m.id,
              role: m.sender === "user" ? "user" : "assistant",
              content: m.content,
              payload: m.metadata,
            }));
            setMessages(formatted);
          }
        } else {
          setMessages([{
            id: "welcome",
            role: "assistant",
            content: "Hi 👋 I'm Daksha. How can I help you shop today?",
          }]);
        }
      } catch (e) {
        console.error("Failed to load history:", e);
        setMessages([{
          id: "welcome",
          role: "assistant",
          content: "Hi 👋 I'm Daksha. How can I help you shop today?",
        }]);
      }
    };

    loadHistory();
  }, [user]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(textOverride = null) {
    const textToSend = textOverride || input;
    if (!textToSend.trim()) return;

    const userMsg = {
      id: crypto.randomUUID(),
      role: "user",
      content: textToSend.trim(),
    };

    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await api.post("/channels/message", {
        channel_type: "web",
        channel_id: getSessionId(),
        message: userMsg.content,
      });

      // Extract reply and payload
      let agentText = "I processed that.";
      let agentPayload = null;
      let confidence = null;

      if (res.data?.reply) {
          if (typeof res.data.reply === 'string') {
              agentText = res.data.reply;
          } else if (typeof res.data.reply === 'object') {
              agentText = res.data.reply.reply || "Here is what I found.";
              agentPayload = res.data.reply.payload || null;
              confidence = res.data.reply.confidence;
          }
      }

      // Extract conversation_id from response if available
      if (res.data.conversation_id && !conversationId) {
        setConversationId(res.data.conversation_id);
      }

      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: agentText,
          payload: agentPayload,
          confidence: confidence,
        },
      ]);

      speak(agentText);

    } catch (e) {
      console.error(e);
      const errText = "I hit a snag connecting. Let's try again.";
      setMessages((m) => [...m, { 
        id: crypto.randomUUID(), 
        role: "assistant", 
        content: errText 
      }]);
      speak(errText);
      toast.error("Failed to send message");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <div className="border-b border-border/40 bg-background/70 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto h-14 px-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div>
              <div className="font-semibold leading-tight">Daksha</div>
              <div className="text-xs text-muted-foreground">AI Sales Assistant</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {conversationId && (
              <Badge variant="outline" className="text-xs">
                Connected
              </Badge>
            )}
            <Button variant="ghost" size="icon" onClick={() => setIsSpeaking(!isSpeaking)}>
               {isSpeaking ? <Volume2 className="h-5 w-5 text-green-500" /> : <VolumeX className="h-5 w-5 text-muted-foreground" />}
            </Button>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
          <AnimatePresence>
            {messages.map((m) => <Message key={m.id} msg={m} />)}
          </AnimatePresence>
          {sending && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground text-center justify-center animate-pulse">
              <Bot className="h-3 w-3" />
              Thinking...
            </div>
          )}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-border/40 bg-background/80 backdrop-blur sticky bottom-0">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-2">
            <Button 
              variant={isListening ? "destructive" : "secondary"} 
              size="icon" 
              onClick={toggleMic} 
              className={`shrink-0 ${isListening ? "animate-pulse" : ""}`}
            >
                {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Input 
              placeholder="Type or speak..." 
              value={input} 
              onChange={(e) => setInput(e.target.value)} 
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()} 
              disabled={sending} 
              className="flex-1"
            />
            <Button onClick={() => sendMessage()} disabled={sending || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
