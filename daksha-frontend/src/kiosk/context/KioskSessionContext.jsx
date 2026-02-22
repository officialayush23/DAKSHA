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

  const [sessionActive, setSessionActive] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // FIX: read kioskId from localStorage on init so it survives navigation
  const [kioskId, _setKioskId] = useState(() => localStorage.getItem('kiosk_id') || null);

  const [user, _setUser] = useState(null);
  const [cartCount, setCartCount] = useState(0);
  const [lastActivity, setLastActivity] = useState(Date.now());

  // FIX: wrap setKioskId to also persist to localStorage
  const setKioskId = useCallback((id) => {
    localStorage.setItem('kiosk_id', id);
    _setKioskId(id);
  }, []);

  const endSession = useCallback((reason = "") => {
    setSessionActive(false);
    setSessionId(null);
    _setUser(null);
    setCartCount(0);
    // FIX: clear kioskId from localStorage on session end
    localStorage.removeItem('kiosk_id');
    _setKioskId(null);
    if (reason) toast.info(reason);
    navigate('/kiosk');
  }, [navigate]);

  const startSession = useCallback(async () => {
    try {
      const res = await KioskService.startSession(CHANNEL_TYPE?.KIOSK || 'kiosk');
      setSessionActive(true);
      setSessionId(res?.session_id || null);
      setLastActivity(Date.now());
      _setUser(null);
      setCartCount(0);
      navigate('/kiosk/select');
    } catch (error) {
      console.error("Failed to start session:", error);
      toast.error("Could not start session. Check connection.");
    }
  }, [navigate]);

  // FIX: setUser also flips sessionActive to true
  const setUser = useCallback((userData) => {
    _setUser(userData);
    setSessionActive(true);
  }, []);

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
    } catch (e) {
      console.warn("Tracking failed", e);
    }
  }, []);

  useEffect(() => {
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

  const value = useMemo(() => ({
    kioskId,
    setKioskId,
    sessionActive,
    sessionId,
    user,
    setUser,
    cartCount,
    setCartCount,
    startSession,
    endSession,
    resetIdleTimer,
    refreshCart,
    trackEvent
  }), [sessionActive, sessionId, kioskId, user, cartCount, startSession, endSession, resetIdleTimer, refreshCart, trackEvent, setUser, setKioskId]);

  return (
    <KioskContext.Provider value={value}>
      {children}
    </KioskContext.Provider>
  );
};