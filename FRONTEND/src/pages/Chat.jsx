// src/pages/Chat.jsx
import React, { useEffect, useRef, useState } from "react";
import api from "@/lib/apiClient";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Sparkles, Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getSessionId } from "@/lib/analytics";
import ChatProductCard from "@/components/chat/ChatProductCard";

// --- SPEECH UTILS ---
const synth = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

// --------------------------------------------------
// Message bubble
// --------------------------------------------------
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
            </div>
          )}
          <div className="whitespace-pre-wrap">{renderContent()}</div>
        </div>

        {/* 🛍️ PRODUCT CAROUSEL */}
        {msg.payload?.type === 'products' && msg.payload.data?.length > 0 && (
          <div className="mt-2 w-full flex gap-2 overflow-x-auto pb-2 pt-1 scrollbar-hide snap-x">
            {msg.payload.data.map(p => (
              <div key={p.id} className="snap-start shrink-0">
                <ChatProductCard product={p} />
              </div>
            ))}
          </div>
        )}

        {/* 📦 ORDER HISTORY / STATUS */}
        {(msg.payload?.type === 'order_status' || msg.payload?.type === 'order_history') && (
             <div className="mt-2 p-3 bg-white/5 rounded-lg border border-white/10 text-xs w-full max-w-xs">
                <div className="font-mono text-gray-400 text-[10px] uppercase">Data Loaded</div>
                <div className="text-green-400 font-bold">
                    {Array.isArray(msg.payload.data) 
                        ? `${msg.payload.data.length} Orders Found` 
                        : `Status: ${msg.payload.data.status}`}
                </div>
             </div>
        )}

      </div>
    </motion.div>
  );
}

// --------------------------------------------------
// Chat Page Main Logic
// --------------------------------------------------
export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(true); 
  const recognitionRef = useRef(null);
  const scrollRef = useRef(null);

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
    
    // 🛡️ Safety Check: Ensure text is a string
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

  useEffect(() => {
    setMessages([{
        id: "welcome",
        role: "assistant",
        content: "Hi 👋 I’m Daksha. How can I help you shop today?",
    }]);
  }, []);

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
        channel_type: "web_cookie",
        channel_id: getSessionId(),
        message: userMsg.content,
      });

      // 🛡️ SAFE EXTRACTION
      let agentText = "I processed that.";
      let agentPayload = null;

      // Extract Reply
      if (res.data?.reply) {
          if (typeof res.data.reply === 'string') {
              agentText = res.data.reply;
          } else if (typeof res.data.reply === 'object') {
              // Extract nested text strictly
              agentText = res.data.reply.reply || "Here is what I found.";
              agentPayload = res.data.reply.payload || null;
          }
      }

      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: agentText,
          payload: agentPayload,
        },
      ]);

      speak(agentText);

    } catch (e) {
      console.error(e);
      const errText = "I hit a snag connecting. Let’s try again.";
      setMessages((m) => [{ id: crypto.randomUUID(), role: "assistant", content: errText }]);
      speak(errText);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <div className="border-b border-border/40 bg-background/70 backdrop-blur">
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
          <Button variant="ghost" size="icon" onClick={() => setIsSpeaking(!isSpeaking)}>
             {isSpeaking ? <Volume2 className="h-5 w-5 text-green-500" /> : <VolumeX className="h-5 w-5 text-muted-foreground" />}
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
          <AnimatePresence>
            {messages.map((m) => <Message key={m.id} msg={m} />)}
          </AnimatePresence>
          {sending && <div className="text-xs text-muted-foreground text-center animate-pulse">Thinking...</div>}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-border/40 bg-background/80 backdrop-blur">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-2">
            <Button variant={isListening ? "destructive" : "secondary"} size="icon" onClick={toggleMic} className={`shrink-0 ${isListening ? "animate-pulse" : ""}`}>
                {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Input placeholder="Type or speak..." value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendMessage()} disabled={sending} />
            <Button onClick={() => sendMessage()} disabled={sending}><Send className="h-4 w-4" /></Button>
          </div>
        </div>
      </div>
    </div>
  );
}