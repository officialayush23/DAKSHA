// src/components/layout/GlobalLayout.jsx
import React, { useState, useRef, useEffect } from "react";
import { Outlet } from "react-router-dom";
import { Bot, Sparkles, Mic, MicOff, Volume2, VolumeX, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { motion } from "framer-motion";
import api from "@/lib/apiClient";
import { getSessionId } from "@/lib/analytics";
import ChatProductCard from "@/components/chat/ChatProductCard";

const synth = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

export function GlobalLayout() {
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    { role: "assistant", content: "Hello! I'm your personal stylist. How can I help?" }
  ]);
  const [isSending, setIsSending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(true); 
  
  const scrollRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.lang = "en-IN";
      recognition.interimResults = false;
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setChatInput(transcript);
        handleGlobalChat(transcript); 
      };
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

  // 🔊 SAFE SPEAK
  const speak = (text) => {
    if (!isSpeaking || !synth) return;
    
    let safeText = "";
    if (typeof text === 'string') safeText = text;
    else if (typeof text === 'object' && text !== null) safeText = text.reply || text.text || "I found some info for you.";
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
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleGlobalChat = async (textOverride = null) => {
    const userText = textOverride || chatInput;
    if (!userText.trim()) return;
    
    setChatMessages(prev => [...prev, { role: "user", content: userText }]);
    setChatInput("");
    setIsSending(true);

    try {
      const res = await api.post("/channels/message", {
        channel_type: "web_cookie",
        channel_id: getSessionId(),
        message: userText
      });
      
      // 🛡️ SAFE EXTRACTION
      let agentText = "I found this.";
      let agentPayload = null;

      if (res.data?.reply) {
          if (typeof res.data.reply === 'string') {
              agentText = res.data.reply;
          } else if (typeof res.data.reply === 'object') {
              agentText = res.data.reply.reply || "Here is what I found.";
              agentPayload = res.data.reply.payload || null;
          }
      }

      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: agentText,
        payload: agentPayload 
      }]);
      
      speak(agentText);

    } catch (err) {
      const errorMsg = "Sorry, I'm having trouble connecting right now.";
      setChatMessages(prev => [...prev, { role: "assistant", content: errorMsg }]);
      speak(errorMsg);
    } finally {
      setIsSending(false);
    }
  };

  // Safe Rendering Helper for text bubbles
  const renderMessageContent = (m) => {
    const content = m.content;
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) return content.map(c => c.text || "").join("\n");
    if (typeof content === 'object' && content !== null) {
        return content.reply || content.text || JSON.stringify(content);
    }
    return String(content);
  };

  return (
    <div className="min-h-screen bg-background font-sans antialiased selection:bg-cyan-500/30">
      <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] opacity-50" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] opacity-50" />
      </div>

      <Outlet />

      <div className="fixed bottom-24 md:bottom-8 right-6 z-50">
        <Sheet>
          <SheetTrigger asChild>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button className="h-16 w-16 rounded-full shadow-[0_0_40px_-10px_rgba(6,182,212,0.6)] bg-gradient-to-br from-cyan-400 to-blue-600 hover:from-cyan-300 hover:to-blue-500 border border-white/20 transition-all duration-300">
                <Bot className="h-8 w-8 text-black" />
                <span className="sr-only">Open AI Assistant</span>
                </Button>
            </motion.div>
          </SheetTrigger>
          
          <SheetContent side="right" className="w-full sm:w-[400px] flex flex-col p-0 border-l border-white/10 bg-black/80 backdrop-blur-2xl">
            <SheetHeader className="px-6 py-5 border-b border-white/10 bg-white/5">
              <SheetTitle className="flex items-center justify-between text-cyan-50">
                <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-cyan-400" />
                    <span className="bg-gradient-to-r from-cyan-200 to-blue-200 bg-clip-text text-transparent font-bold">Daksha AI</span>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsSpeaking(!isSpeaking)}>
                    {isSpeaking ? <Volume2 className="h-4 w-4 text-green-400" /> : <VolumeX className="h-4 w-4 text-muted-foreground" />}
                </Button>
              </SheetTitle>
            </SheetHeader>
            
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              {chatMessages.map((m, i) => (
                <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${m.role === 'assistant' ? 'bg-cyan-500/20 border-cyan-500/30' : 'bg-purple-500/20'}`}>
                     {m.role === 'assistant' ? <Bot className="h-5 w-5 text-cyan-400" /> : <div className="h-2 w-2 rounded-full bg-purple-400" />}
                  </div>
                  
                  <div className={`flex flex-col max-w-[85%]`}>
                      <div className={`p-3 rounded-2xl text-sm ${m.role === 'assistant' ? 'bg-white/10 border-white/5 rounded-tl-none text-gray-200' : 'bg-cyan-600 text-white rounded-tr-none'}`}>
                        <div className="whitespace-pre-wrap">{renderMessageContent(m)}</div>
                      </div>

                      {m.role === 'assistant' && m.payload?.type === 'products' && m.payload.data?.length > 0 && (
                          <div className="mt-2 flex gap-2 overflow-x-auto pb-2 scrollbar-hide -mx-1 px-1 snap-x">
                            {m.payload.data.map(p => (
                              <div key={p.id} className="snap-start shrink-0 scale-90 origin-top-left">
                                <ChatProductCard product={p} />
                              </div>
                            ))}
                          </div>
                      )}
                  </div>
                </div>
              ))}
              {isSending && <div className="text-xs text-muted-foreground animate-pulse ml-12">Thinking...</div>}
              <div ref={scrollRef} />
            </div>

            <div className="p-4 border-t border-white/10 bg-black/40">
               <div className="flex gap-2">
                 <Button variant={isListening ? "destructive" : "secondary"} size="icon" onClick={toggleMic} className={`shrink-0 rounded-full h-10 w-10 ${isListening ? "animate-pulse" : "bg-white/10 border border-white/10 hover:bg-white/20"}`}>
                    {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                 </Button>
                 <div className="relative flex-1">
                    <input 
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleGlobalChat()}
                        className="w-full h-10 bg-white/5 border border-white/10 rounded-full pl-4 pr-10 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all"
                        placeholder="Type or speak..."
                        disabled={isSending}
                    />
                    <Button size="icon" variant="ghost" className="absolute right-1 top-1 h-8 w-8 rounded-full hover:bg-cyan-500/20 text-cyan-400" onClick={() => handleGlobalChat()} disabled={isSending}>
                        <Send className="h-4 w-4" />
                    </Button>
                 </div>
               </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  );
}