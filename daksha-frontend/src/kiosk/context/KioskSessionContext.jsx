import React, { createContext, useContext, useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { KioskService } from '@/lib/kioskApi';
import { KIOSK_CONFIG, CHANNEL_TYPE } from '../constants';

const KioskContext = createContext();

export const useKiosk = () => useContext(KioskContext);

export const KioskProvider = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const idleTimerRef = useRef(null);
  
  // State
  const [sessionActive, setSessionActive] = useState(false);
  const [user, setUser] = useState(null);
  const [cartCount, setCartCount] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());

  // --- 1. MEMOIZED ACTIONS (Prevents Infinite Loops) ---

  const endSession = useCallback((reason = "") => {
    setSessionActive(false);
    setUser(null);
    setCartCount(0);
    if (reason) toast.info(reason);
    navigate('/kiosk'); // Redirect to Attract Screen
  }, [navigate]);

  const startSession = useCallback(async () => {
    try {
      // API: POST /session/start?channel=kiosk
      await KioskService.startSession(CHANNEL_TYPE?.KIOSK || 'kiosk');
      setSessionActive(true);
      setLastActivity(Date.now());
      setUser(null);
      setCartCount(0);
      navigate('/kiosk/login');
    } catch (error) {
      console.error("Failed to start session:", error);
      toast.error("Could not start session. Check connection.");
    }
  }, [navigate]);

  const resetIdleTimer = useCallback(() => {
    setLastActivity(Date.now());
  }, []);

  const refreshCart = useCallback(async () => {
    try {
      const cart = await KioskService.getCart();
      const items = cart.items || [];
      const count = items.reduce((acc, item) => acc + item.quantity, 0);
      setCartCount(count);
    } catch (error) {
      console.error("Cart refresh failed:", error);
    }
  }, []);

  const trackEvent = useCallback(async (eventType, entityType, entityId) => {
    try {
      console.log(`[Tracking] ${eventType} - ${entityType}:${entityId}`);
      // await KioskService.captureEvent(...)
    } catch (e) {
      console.warn("Tracking failed", e);
    }
  }, []);

  // --- 2. IDLE TIMER EFFECT ---
  useEffect(() => {
    // Don't run timer on Attract Screen
    if (location.pathname === '/kiosk' || location.pathname === '/kiosk/') return;

    const timeoutMs = KIOSK_CONFIG?.IDLE_TIMEOUT_MS || 60000;

    const checkInactivity = () => {
      if (Date.now() - lastActivity > timeoutMs) {
        endSession("Session timed out");
      }
    };

    idleTimerRef.current = setInterval(checkInactivity, 5000); 

    return () => {
      if (idleTimerRef.current) clearInterval(idleTimerRef.current);
    };
  }, [lastActivity, location.pathname, endSession]);

  // --- 3. MEMOIZED VALUE (Crucial) ---
  const value = useMemo(() => ({
    kioskId: KIOSK_CONFIG?.KIOSK_ID || 'KIOSK_01',
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
  }), [sessionActive, user, cartCount, startSession, endSession, resetIdleTimer, refreshCart, trackEvent]);

  return (
    <KioskContext.Provider value={value}>
      {children}
    </KioskContext.Provider>
  );
};