// src/components/GoogleMapsStorePicker.jsx
// Google Maps store picker — emoji markers, distance badges, animated popups
import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, MapPin, Package, Navigation, Store, Star } from 'lucide-react';
import { toast } from 'sonner';

const GMAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';
const API_BASE  = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── Inject Google Maps script once ──────────────────────────────────────────
let _gmapsLoaded = false;
let _gmapsCallbacks = [];

function loadGoogleMaps(apiKey) {
  return new Promise((resolve) => {
    if (window.google?.maps) { resolve(); return; }
    if (_gmapsLoaded) { _gmapsCallbacks.push(resolve); return; }
    _gmapsLoaded = true;
    _gmapsCallbacks.push(resolve);
    window.__gmapsReady = () => _gmapsCallbacks.forEach(fn => fn());
    const s = document.createElement('script');
    s.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places,geometry&callback=__gmapsReady`;
    s.async = true; s.defer = true;
    document.head.appendChild(s);
  });
}

// ── Distance formatter ────────────────────────────────────────────────────────
function fmtDist(km) {
  if (km == null) return '';
  if (km < 1) return `${Math.round(km * 1000)} m`;
  return `${km.toFixed(1)} km`;
}

// ── Marker HTML builder ───────────────────────────────────────────────────────
function buildMarkerEl(store, isSelected) {
  const hasStock = store.available_stock > 0;
  const ring    = isSelected ? '3px solid #a78bfa' : `2px solid ${hasStock ? '#34d399' : '#f87171'}`;
  const shadow  = isSelected
    ? '0 0 0 4px rgba(167,139,250,0.35), 0 4px 16px rgba(0,0,0,0.6)'
    : '0 2px 8px rgba(0,0,0,0.5)';

  const el = document.createElement('div');
  el.style.cssText = `
    display: flex; flex-direction: column; align-items: center;
    cursor: pointer; transform-origin: bottom center;
    transition: transform 0.2s cubic-bezier(.34,1.56,.64,1);
    transform: scale(${isSelected ? 1.25 : 1});
  `;
  el.innerHTML = `
    <div style="
      background: ${isSelected ? '#1e1b4b' : hasStock ? '#064e3b' : '#450a0a'};
      border: ${ring};
      border-radius: 50%;
      width: 48px; height: 48px;
      display: flex; align-items: center; justify-content: center;
      box-shadow: ${shadow};
      font-size: 22px;
      line-height: 1;
    ">🏪</div>
    ${store.distance_km != null ? `
    <div style="
      background: ${isSelected ? '#7c3aed' : hasStock ? '#065f46' : '#7f1d1d'};
      color: white;
      font-size: 10px; font-weight: 700;
      padding: 2px 7px; border-radius: 99px;
      margin-top: 3px; white-space: nowrap;
      box-shadow: 0 1px 4px rgba(0,0,0,0.4);
      letter-spacing: 0.3px;
    ">${fmtDist(store.distance_km)}</div>` : ''}
    <div style="
      width: 2px; height: 8px;
      background: ${isSelected ? '#7c3aed' : hasStock ? '#065f46' : '#7f1d1d'};
      margin-top: 1px;
    "></div>
    <div style="
      width: 6px; height: 3px;
      background: radial-gradient(ellipse,rgba(0,0,0,0.4) 0%,transparent 80%);
      border-radius: 50%;
    "></div>
  `;
  return el;
}

// ── Info-window HTML ─────────────────────────────────────────────────────────
function buildInfoWindowContent(store) {
  const hasStock = store.available_stock > 0;
  return `
    <div style="
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      padding: 12px 14px; min-width: 220px; max-width: 280px;
      background: #18181b; color: #f4f4f5; border-radius: 10px;
    ">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <span style="font-size:18px">🏪</span>
        <div>
          <p style="margin:0;font-weight:700;font-size:14px;color:#f4f4f5">${store.name}</p>
          ${store.city ? `<p style="margin:0;font-size:11px;color:#71717a">${store.city}${store.state ? ', ' + store.state : ''}</p>` : ''}
        </div>
      </div>
      ${store.address ? `<p style="margin:0 0 8px;font-size:11px;color:#a1a1aa;line-height:1.4">${store.address}</p>` : ''}
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <span style="
          font-size:11px;font-weight:600;
          color:${hasStock ? '#34d399' : '#f87171'};
          background:${hasStock ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)'};
          padding:3px 9px;border-radius:99px;
          border:1px solid ${hasStock ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)'};
        ">
          ${hasStock ? `📦 ${store.available_stock} in stock` : '❌ Out of stock'}
        </span>
        ${store.distance_km != null ? `
        <span style="font-size:11px;color:#71717a;display:flex;align-items:center;gap:3px">
          📍 ${fmtDist(store.distance_km)} away
        </span>` : ''}
      </div>
    </div>
  `;
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Props:
 *   cartItems    — array of { product_variant_id, quantity }
 *   onStoreSelect — callback(store) when user confirms pickup location
 *   onClose      — close the modal
 */
export default function GoogleMapsStorePicker({ cartItems = [], onStoreSelect, onClose }) {
  const mapContainer = useRef(null);
  const mapRef       = useRef(null);
  const markersRef   = useRef({});     // store.id → { overlay, el }
  const infoWindowRef = useRef(null);

  const [gmapsReady, setGmapsReady] = useState(!!window.google?.maps);
  const [loading, setLoading]       = useState(true);
  const [stores, setStores]         = useState([]);
  const [selected, setSelected]     = useState(null);
  const [userCoords, setUserCoords] = useState(null);

  // ── Load Google Maps ────────────────────────────────────────────────────────
  useEffect(() => {
    if (window.google?.maps) { setGmapsReady(true); return; }
    loadGoogleMaps(GMAPS_KEY).then(() => setGmapsReady(true));
  }, []);

  // ── Get user location ────────────────────────────────────────────────────────
  useEffect(() => {
    if (!navigator.geolocation) {
      setUserCoords({ lat: 12.9716, lng: 77.5946 });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => setUserCoords({ lat: coords.latitude, lng: coords.longitude }),
      () => setUserCoords({ lat: 12.9716, lng: 77.5946 }),
      { timeout: 5000 }
    );
  }, []);

  // ── Fetch nearby stores ──────────────────────────────────────────────────────
  const fetchStores = useCallback(async (lat, lng) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ lat, lng, radius_km: 25 });
      const res = await fetch(`${API_BASE}/stores/nearby?${params}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const data = await res.json();
      setStores(Array.isArray(data) ? data : []);
    } catch {
      toast.error('Could not load nearby stores');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (userCoords) fetchStores(userCoords.lat, userCoords.lng);
  }, [userCoords, fetchStores]);

  // ── Init Google Map ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!gmapsReady || !userCoords || mapRef.current) return;
    const { Map, InfoWindow } = window.google.maps;

    const map = new Map(mapContainer.current, {
      center: { lat: userCoords.lat, lng: userCoords.lng },
      zoom: 13,
      mapId: 'daksha_store_map',
      disableDefaultUI: false,
      zoomControl: true,
      streetViewControl: false,
      mapTypeControl: false,
      fullscreenControl: false,
      styles: [
        { elementType: 'geometry', stylers: [{ color: '#18181b' }] },
        { elementType: 'labels.text.stroke', stylers: [{ color: '#18181b' }] },
        { elementType: 'labels.text.fill', stylers: [{ color: '#a1a1aa' }] },
        { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#27272a' }] },
        { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#212121' }] },
        { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#71717a' }] },
        { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#3f3f46' }] },
        { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0f172a' }] },
        { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#515c6d' }] },
        { featureType: 'poi', stylers: [{ visibility: 'off' }] },
        { featureType: 'transit', stylers: [{ visibility: 'off' }] },
        { featureType: 'administrative', elementType: 'geometry', stylers: [{ color: '#3f3f46' }] },
      ],
    });

    infoWindowRef.current = new InfoWindow({ disableAutoPan: false });

    // User location pulse marker
    const userEl = document.createElement('div');
    userEl.innerHTML = `
      <div style="position:relative;width:20px;height:20px">
        <div style="
          position:absolute;inset:0;border-radius:50%;
          background:rgba(124,58,237,0.25);
          animation:pulse 2s infinite;
        "></div>
        <div style="
          position:absolute;inset:4px;border-radius:50%;
          background:#7c3aed;border:2px solid white;
          box-shadow:0 0 0 2px rgba(124,58,237,0.5);
        "></div>
        <style>
          @keyframes pulse{0%,100%{transform:scale(1);opacity:0.6}50%{transform:scale(2.2);opacity:0}}
        </style>
      </div>
    `;
    new window.google.maps.marker.AdvancedMarkerElement({
      map, position: { lat: userCoords.lat, lng: userCoords.lng },
      content: userEl,
      title: 'You are here',
    }).catch?.(() => {
      // Fallback if AdvancedMarkerElement unavailable
      new window.google.maps.Marker({
        map, position: { lat: userCoords.lat, lng: userCoords.lng },
        icon: { path: window.google.maps.SymbolPath.CIRCLE, scale: 8, fillColor: '#7c3aed', fillOpacity: 1, strokeColor: 'white', strokeWeight: 2 },
        title: 'You are here',
      });
    });

    mapRef.current = map;
    return () => { map = null; mapRef.current = null; };
  }, [gmapsReady, userCoords]);

  // ── Place store markers ──────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !stores.length || !gmapsReady) return;

    // Remove old markers
    Object.values(markersRef.current).forEach(({ overlay }) => overlay.setMap?.(null));
    markersRef.current = {};

    stores.forEach((store) => {
      if (!store.latitude || !store.longitude) return;

      const isSelected = selected?.id === store.id;
      const el = buildMarkerEl(store, isSelected);

      let marker;
      try {
        marker = new window.google.maps.marker.AdvancedMarkerElement({
          map,
          position: { lat: store.latitude, lng: store.longitude },
          content: el,
          title: store.name,
        });
        marker.addListener('click', () => handleMarkerClick(store));
      } catch {
        // Fallback to classic Marker
        marker = new window.google.maps.Marker({
          map,
          position: { lat: store.latitude, lng: store.longitude },
          title: store.name,
          icon: {
            url: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"><text y="32" font-size="30">🏪</text></svg>`,
            scaledSize: new window.google.maps.Size(40, 40),
            anchor: new window.google.maps.Point(20, 40),
          },
        });
        marker.addListener('click', () => handleMarkerClick(store));
      }

      markersRef.current[store.id] = { overlay: marker, el };
    });
  }, [stores, gmapsReady]);

  // Update marker appearance when selection changes
  useEffect(() => {
    stores.forEach((store) => {
      const entry = markersRef.current[store.id];
      if (!entry) return;
      const isSelected = selected?.id === store.id;
      const newEl = buildMarkerEl(store, isSelected);
      if (entry.overlay.content !== undefined) {
        entry.overlay.content = newEl;
        entry.el = newEl;
      }
    });
  }, [selected]);

  const handleMarkerClick = useCallback((store) => {
    const map = mapRef.current;
    if (!map) return;

    setSelected(store);
    infoWindowRef.current.setContent(buildInfoWindowContent(store));

    // Open on the marker
    const entry = markersRef.current[store.id];
    if (entry?.overlay) {
      infoWindowRef.current.open({ map, anchor: entry.overlay });
    }

    map.panTo({ lat: store.latitude, lng: store.longitude });
    map.panBy(0, -80);
  }, []);

  const handleConfirm = () => {
    if (!selected) return;
    onStoreSelect(selected);
    toast.success(`Store selected: ${selected.name}`);
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full" style={{ minHeight: 480 }}>
      {/* Map */}
      <div className="relative flex-1 min-h-0" style={{ minHeight: 340 }}>
        {(loading || !gmapsReady) && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-zinc-950/80 rounded-t-xl gap-2">
            <Loader2 className="h-7 w-7 animate-spin text-violet-400" />
            <p className="text-xs text-zinc-500">
              {!gmapsReady ? 'Loading maps…' : 'Finding stores near you…'}
            </p>
          </div>
        )}
        <div ref={mapContainer} className="w-full h-full rounded-t-xl" style={{ minHeight: 340 }} />

        {/* Store count badge overlay */}
        {!loading && stores.length > 0 && (
          <div className="absolute top-3 left-3 z-10 bg-zinc-900/90 backdrop-blur-sm border border-zinc-700 rounded-lg px-3 py-1.5 flex items-center gap-2">
            <Store className="h-3.5 w-3.5 text-violet-400" />
            <span className="text-xs font-medium text-zinc-300">
              {stores.length} stores within 25 km
            </span>
          </div>
        )}
      </div>

      {/* Store list strip */}
      {!selected && stores.length > 0 && (
        <div className="bg-zinc-900 border-t border-zinc-800 px-3 py-2 flex gap-2 overflow-x-auto scrollbar-hide">
          {stores.slice(0, 6).map((store) => (
            <button
              key={store.id}
              onClick={() => handleMarkerClick(store)}
              className="flex-shrink-0 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg px-3 py-2 text-left transition-colors group"
              style={{ minWidth: 160 }}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-base">🏪</span>
                <p className="text-xs font-semibold text-zinc-200 truncate">{store.name}</p>
              </div>
              <div className="flex items-center gap-2">
                {store.distance_km != null && (
                  <span className="text-[10px] text-violet-400 font-medium">
                    {fmtDist(store.distance_km)}
                  </span>
                )}
                <span className={`text-[10px] font-medium ${store.available_stock > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {store.available_stock > 0 ? `${store.available_stock} in stock` : 'Out of stock'}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Bottom action strip */}
      <div className="bg-zinc-900 border-t border-zinc-800 px-4 py-3 rounded-b-xl">
        {selected ? (
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-start gap-2.5 min-w-0">
              <div className="text-2xl mt-0.5">🏪</div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-zinc-100 truncate">{selected.name}</p>
                <p className="text-xs text-zinc-500 truncate">{selected.address}</p>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <Badge className={`text-[10px] px-1.5 py-0 ${
                    selected.available_stock > 0
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : 'bg-red-500/15 text-red-400 border-red-500/30'
                  }`}>
                    <Package className="h-2.5 w-2.5 mr-1" />
                    {selected.available_stock > 0
                      ? `${selected.available_stock} items available`
                      : 'Out of stock'}
                  </Badge>
                  {selected.distance_km != null && (
                    <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                      <Navigation className="h-2.5 w-2.5" />
                      {fmtDist(selected.distance_km)} away
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <Button
                variant="outline" size="sm"
                onClick={() => { setSelected(null); infoWindowRef.current?.close(); }}
                className="text-xs border-zinc-700 h-8"
              >
                Change
              </Button>
              <Button
                size="sm"
                onClick={handleConfirm}
                disabled={!selected.available_stock}
                className="text-xs bg-violet-600 hover:bg-violet-700 h-8"
              >
                Pick up here
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <MapPin className="h-4 w-4 text-violet-400" />
            {loading
              ? 'Finding stores near you…'
              : stores.length === 0
                ? 'No stores found nearby — try a wider radius'
                : 'Tap a 🏪 pin or card to select a pickup store'}
          </div>
        )}
      </div>
    </div>
  );
}
