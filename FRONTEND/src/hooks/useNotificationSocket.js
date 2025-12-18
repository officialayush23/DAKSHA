import { useEffect, useRef } from 'react';
import { toast } from "sonner";
import { getSessionId } from '@/lib/analytics';
import { supabase } from "@/lib/supabaseClient";

// ⚠️ Ensure your VITE_WS_URL is set in .env (e.g. ws://localhost:8000)
// If undefined, it falls back to current origin but with ws protocol
const getWsUrl = () => {
    if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.hostname}:8000`; // Assuming backend on 8000
};

export function useNotificationSocket(onNotification) {
  const socketRef = useRef(null);

  useEffect(() => {
    const connect = async () => {
        // 1. Get Real User ID if logged in, else Session ID
        const { data: { user } } = await supabase.auth.getUser();
        const userId = user?.id || getSessionId();

        if (!userId) return;

        // 2. Connect
        const url = `${getWsUrl()}/ws/notifications/${userId}`;
        console.log("🔌 Connecting WS:", url);
        
        const ws = new WebSocket(url);
        socketRef.current = ws;

        ws.onopen = () => {
            console.log(`✅ Notification Stream Active: ${userId}`);
        };

        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                
                // Show Toast
                toast(payload.title || "Notification", {
                    description: payload.body,
                    action: payload.link ? {
                        label: "View",
                        onClick: () => window.location.href = payload.link
                    } : undefined,
                });

                if (onNotification) onNotification(payload);

            } catch (err) {
                console.error("WS Parse Error:", err);
            }
        };

        ws.onerror = (e) => {
            console.warn("WS Error (Backend likely offline):", e);
        };

        ws.onclose = () => console.log("🔕 WS Disconnected");
    };

    connect();

    return () => {
        if (socketRef.current) socketRef.current.close();
    };
  }, []);

  return socketRef.current;
}