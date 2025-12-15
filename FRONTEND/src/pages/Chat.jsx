// src/pages/Chat.jsx
import React, { useEffect, useRef, useState } from "react";
import api from "@/lib/apiClient";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, Sparkles, ShoppingBag } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

// --------------------------------------------------
// Message bubble
// --------------------------------------------------
function Message({ msg }) {
  const isUser = msg.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed
        ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-card border border-border/40"
        }`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-1 text-xs text-muted-foreground">
            <Bot className="h-3.5 w-3.5" />
            Daksha
          </div>
        )}
        <div>{msg.content}</div>

        {/* Agent reasoning / metadata */}
        {msg.meta?.reason && (
          <div className="mt-2 text-xs text-muted-foreground bg-muted/40 rounded-md p-2">
            {msg.meta.reason}
          </div>
        )}

        {/* Action buttons (future-ready) */}
        {msg.meta?.actions?.length > 0 && (
          <div className="mt-3 flex gap-2 flex-wrap">
            {msg.meta.actions.map((a) => (
              <Button
                key={a.label}
                size="sm"
                variant="outline"
                onClick={() => a.onClick?.()}
              >
                {a.icon && <a.icon className="h-3 w-3 mr-1" />}
                {a.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// --------------------------------------------------
// Chat Page
// --------------------------------------------------
export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  // Initial greeting
  useEffect(() => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          "Hi 👋 I’m Daksha, your personal sales assistant. What are you shopping for today?",
      },
    ]);
  }, []);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // --------------------------------------------------
  // Send message (API wired, agent later)
  // --------------------------------------------------
  async function sendMessage() {
    if (!input.trim()) return;

    const userMsg = {
      id: crypto.randomUUID(),
      role: "user",
      content: input.trim(),
    };

    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);

    try {
      const res = await api.post("/chat/message", {
        message: userMsg.content,
      });

      const agentReply = res.data;

      setMessages((m) => [
        ...m,
        {
          id: agentReply.id || crypto.randomUUID(),
          role: "assistant",
          content: agentReply.text,
          meta: agentReply.meta,
        },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "I hit a snag processing that. Let’s try again or refine what you’re looking for.",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Header */}
      <div className="border-b border-border/40 bg-background/70 backdrop-blur">
        <div className="max-w-4xl mx-auto h-14 px-4 flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div>
            <div className="font-semibold leading-tight">Daksha</div>
            <div className="text-xs text-muted-foreground">
              AI Sales Assistant
            </div>
          </div>
        </div>
      </div>

      {/* Conversation */}
      <ScrollArea className="flex-1">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
          <AnimatePresence>
            {messages.map((m) => (
              <Message key={m.id} msg={m} />
            ))}
          </AnimatePresence>
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t border-border/40 bg-background/80 backdrop-blur">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-2">
            <Input
              placeholder="Ask about products, styles, availability, offers…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={sending}
            />
            <Button onClick={sendMessage} disabled={sending}>
              <Send className="h-4 w-4" />
            </Button>
          </div>

          {/* Intent hints */}
          <div className="mt-3 flex gap-2 flex-wrap">
            {[
              "Show me trending items",
              "Recommend something under ₹2000",
              "I need a gift",
            ].map((q) => (
              <Badge
                key={q}
                variant="outline"
                className="cursor-pointer hover:bg-muted"
                onClick={() => setInput(q)}
              >
                {q}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
