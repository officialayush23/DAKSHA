// src/hooks/useInventorySocket.js
import { useEffect, useRef } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export function useInventorySocket(locationId, onUpdate) {
  const socketRef = useRef(null);

  useEffect(() => {
    if (!locationId) return;

    // Connect to specific fulfillment location channel
    const ws = new WebSocket(`${WS_URL}/ws/inventory/${locationId}`);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log(`🟢 WS Connected: Inventory [${locationId}]`);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        // Payload format from redis_bus.py: { type: "inventory_update", data: { ... } }
        if (payload.type === "inventory_update" && onUpdate) {
          onUpdate(payload.data);
        }
      } catch (err) {
        console.error("WS Parse Error:", err);
      }
    };

    ws.onclose = () => console.log("🔴 WS Disconnected");

    return () => {
      ws.close();
    };
  }, [locationId, onUpdate]);

  return socketRef.current;
}