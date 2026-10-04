// src/lib/authToken.js
// One place that decides which bearer token a request uses.
//  • On /kiosk routes, a short-lived kiosk token (phone + OTP) wins, so a kiosk never
//    rides on whatever Supabase session the browser happens to have.
//  • Everywhere else: the Supabase access token.
import { supabase } from './supabaseClient';

const KIOSK_KEY = 'kiosk_token';

export const setKioskToken = (token, expiresInSec) => {
  try {
    sessionStorage.setItem(KIOSK_KEY, JSON.stringify({ token, exp: Date.now() + (expiresInSec || 1800) * 1000 }));
  } catch { /* storage blocked */ }
};

export const clearKioskToken = () => {
  try { sessionStorage.removeItem(KIOSK_KEY); } catch { /* ignore */ }
};

export const getKioskToken = () => {
  try {
    const raw = JSON.parse(sessionStorage.getItem(KIOSK_KEY) || 'null');
    if (raw && raw.exp > Date.now()) return raw.token;
  } catch { /* ignore */ }
  return null;
};

export const isKioskRoute = () => window.location.pathname.startsWith('/kiosk');

export const getAccessToken = async () => {
  if (isKioskRoute()) {
    const k = getKioskToken();
    if (k) return k;
  }
  const { data } = await supabase.auth.getSession();
  return data?.session?.access_token || null;
};

// Which channel is this client? Used by the agents' unified context.
export const detectChannel = () => {
  if (isKioskRoute()) return 'kiosk';
  try {
    if (window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone) return 'pwa';
  } catch { /* ignore */ }
  return 'web';
};

export const wsBase = () => (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/^http/, 'ws');
