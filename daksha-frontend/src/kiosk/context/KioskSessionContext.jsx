import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { KioskService } from '@/lib/kioskApi';
import { KIOSK_CONFIG, CHANNEL_TYPE, EVENT_TYPE } from '../constants';

const KioskContext = createContext();

export const useKiosk = () => useContext(KioskContext);

export const KioskProvider = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const idleTimerRef = useRef(null);
  
  // State
  const [sessionActive, setSessionActive] = useState(false);
  const [user, setUser] = useState(null); // Will be populated after QR scan
  const [cartCount, setCartCount] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());

  // --- Session Management ---

  // Start new anonymous session
  const startSession = async () => {
    try {
      // API: POST /session/start?channel=kiosk
      await KioskService.startSession(CHANNEL_TYPE.KIOSK);
      setSessionActive(true);
      setLastActivity(Date.now());
      setUser(null); // Reset user, wait for binding
      setCartCount(0);
      navigate('/kiosk/login');
    } catch (error) {
      console.error("Failed to start session:", error);
      toast.error("Could not start kiosk session. Check network.");
    }
  };

  // End session (Logout / Timeout)
  const endSession = useCallback(async (reason = "") => {
    setSessionActive(false);
    setUser(null);
    setCartCount(0);
    
    // Optional: Call backend to explicitly close if needed
    // await KioskService.endSession(); 

    if (reason) toast.info(reason);
    navigate('/kiosk'); // Go back to Attract Screen
  }, [navigate]);

  // --- Idle Timer Logic ---
  const resetIdleTimer = useCallback(() => {
    setLastActivity(Date.now());
  }, []);

  useEffect(() => {
    // Don't run idle timer on Attract Screen (inactive state)
    if (location.pathname === '/kiosk' || location.pathname === '/kiosk/') return;

    const checkInactivity = () => {
      if (Date.now() - lastActivity > KIOSK_CONFIG.IDLE_TIMEOUT_MS) {
        endSession("Session timed out due to inactivity");
      }
    };

    idleTimerRef.current = setInterval(checkInactivity, 5000); // Check every 5s

    return () => {
      if (idleTimerRef.current) clearInterval(idleTimerRef.current);
    };
  }, [lastActivity, location.pathname, endSession]);

  // --- Cart Management ---
  const refreshCart = async () => {
    try {
      const cart = await KioskService.getCart();
      // Assuming cart API returns { items: [...] } or array
      const items = cart.items || [];
      const count = items.reduce((acc, item) => acc + item.quantity, 0);
      setCartCount(count);
    } catch (error) {
      console.error("Failed to refresh cart:", error);
    }
  };

  // --- Event Tracking Wrapper ---
  const trackEvent = async (eventType, entityType, entityId, reason = null) => {
    try {
      // Using generic apiClient or specific KioskService method if we added one
      // Since Capture Event is a user API, we can use KioskService (which uses same base client)
      // We might need to add captureEvent to kioskApi.js if not present, or use raw fetch
      // For now assuming KioskService handles auth injection automatically
      console.log(`[Tracking] ${eventType} - ${entityType}:${entityId}`);
    } catch (e) {
      console.warn("Tracking failed", e);
    }
  };

  const value = {
    kioskId: KIOSK_CONFIG.KIOSK_ID,
    sessionActive,
    user,
    setUser,
    cartCount,
    setCartCount,
    startSession,
    endSession,
    resetIdleTimer,
    refreshCart,
    trackEvent
  };

  return (
    <KioskContext.Provider value={value}>
      {children}
    </KioskContext.Provider>
  );
};