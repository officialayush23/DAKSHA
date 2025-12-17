// src/hooks/useNotificationSocket.js
import { useEffect, useRef } from 'react';
import { toast } from "sonner";
import { getSessionId } from '@/lib/analytics'; // Using session/user ID

// Adjust this URL to match your backend (ws://localhost:8000)
const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export function useNotificationSocket(onNotification) {
  const socketRef = useRef(null);

  useEffect(() => {
    const connect = () => {
        const userId = getSessionId(); // Or supabase.auth.getUser().id
        if (!userId) return;

        // Connect to user-specific channel
        const ws = new WebSocket(`${WS_URL}/ws/notifications/${userId}`);
        socketRef.current = ws;

        ws.onopen = () => {
            console.log(`🔔 Notification Stream Connected: ${userId}`);
        };

        ws.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                // Expected Payload: { type: "promotion", title: "New Offer!", body: "..." }
                
                // 1. Trigger Toast Immediately
                toast(payload.title, {
                    description: payload.body,
                    action: {
                        label: "View",
                        onClick: () => window.location.href = '/profile?tab=notifications'
                    },
                });

                // 2. Pass to parent (e.g., to update Badge count)
                if (onNotification) onNotification(payload);

            } catch (err) {
                console.error("Notification Parse Error:", err);
            }
        };

        ws.onclose = () => console.log("🔕 Notification Stream Disconnected");
    };

    connect();

    return () => {
        if (socketRef.current) socketRef.current.close();
    };
  }, []);

  return socketRef.current;
}