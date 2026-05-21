// src/components/MapboxStorePicker.jsx
// Mapbox GL JS store picker — shows nearest stores with stock availability
// Used in the pickup checkout flow to replace the dropdown.
import React, { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, MapPin, Package, Navigation } from 'lucide-react';
import { toast } from 'sonner';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';
const API_BASE     = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Props:
 *   cartItems    — array of { product_variant_id, quantity } to check stock against
 *   onStoreSelect — callback(store) called when user confirms a store
 *   onClose      — close the picker modal
 */
export default function MapboxStorePicker({ cartItems = [], onStoreSelect, onClose }) {
  const mapContainer = useRef(null);
  const mapRef       = useRef(null);
  const markersRef   = useRef([]);
  const popupRef     = useRef(null);

  const [loading, setLoading]   = useState(true);
  const [stores, setStores]     = useState([]);
  const [selected, setSelected] = useState(null);
  const [userCoords, setUserCoords] = useState(null);

  // ── Get user location ────────────────────────────────────────────────────
  useEffect(() => {
    if (!navigator.geolocation) {
      toast.error('Geolocation not supported — showing all stores');
      setUserCoords({ lat: 12.9716, lng: 77.5946 }); // Bangalore default
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => setUserCoords({ lat: coords.latitude, lng: coords.longitude }),
      () => {
        toast.error('Location access denied — showing all stores');
        setUserCoords({ lat: 12.9716, lng: 77.5946 });
      },
      { timeout: 5000 }
    );
  }, []);

  // ── Fetch nearby stores once we have coords ──────────────────────────────
  const fetchStores = useCallback(async (lat, lng) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ lat, lng, radius_km: 20 });
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

  // ── Init Mapbox ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!userCoords || mapRef.current) return;
    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [userCoords.lng, userCoords.lat],
      zoom: 12,
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // User location dot
    new mapboxgl.Marker({ color: '#6d28d9', scale: 0.8 })
      .setLngLat([userCoords.lng, userCoords.lat])
      .setPopup(new mapboxgl.Popup({ offset: 25 }).setText('You are here'))
      .addTo(map);

    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, [userCoords]);

  // ── Add store markers once stores + map are ready ───────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !stores.length) return;

    // Remove old markers
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    stores.forEach((store) => {
      if (!store.latitude || !store.longitude) return;

      const hasStock = store.available_stock > 0;
      const el = document.createElement('div');
      el.className = 'store-marker';
      el.innerHTML = `
        <div style="
          background: ${hasStock ? '#16a34a' : '#dc2626'};
          border: 2px solid ${hasStock ? '#4ade80' : '#f87171'};
          border-radius: 50%;
          width: 20px; height: 20px;
          cursor: pointer;
          box-shadow: 0 0 0 3px ${hasStock ? 'rgba(74,222,128,0.3)' : 'rgba(248,113,113,0.3)'}
        "></div>
      `;

      const popup = new mapboxgl.Popup({ offset: 25, closeButton: false })
        .setHTML(`
          <div style="font-family:sans-serif;padding:4px 2px;min-width:180px">
            <p style="font-weight:600;font-size:13px;margin:0 0 4px">${store.name}</p>
            <p style="font-size:11px;color:#9ca3af;margin:0 0 6px">${store.address || ''}</p>
            <div style="display:flex;align-items:center;gap:6px">
              <span style="
                font-size:11px;font-weight:500;
                color:${hasStock ? '#4ade80' : '#f87171'};
                background:${hasStock ? 'rgba(74,222,128,0.1)' : 'rgba(248,113,113,0.1)'};
                padding:2px 8px;border-radius:99px;
              ">${hasStock ? `${store.available_stock} in stock` : 'Out of stock'}</span>
              ${store.distance_km ? `<span style="font-size:10px;color:#6b7280">${store.distance_km.toFixed(1)} km</span>` : ''}
            </div>
          </div>
        `);

      const marker = new mapboxgl.Marker({ element: el })
        .setLngLat([store.longitude, store.latitude])
        .setPopup(popup)
        .addTo(map);

      el.addEventListener('click', () => {
        popupRef.current?.remove();
        marker.togglePopup();
        popupRef.current = popup;
        setSelected(store);
        map.flyTo({ center: [store.longitude, store.latitude], zoom: 14, duration: 800 });
      });

      markersRef.current.push(marker);
    });
  }, [stores, mapRef.current]);

  const handleConfirm = () => {
    if (!selected) return;
    onStoreSelect(selected);
    toast.success(`Store selected: ${selected.name}`);
  };

  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full">
      {/* Map */}
      <div className="relative flex-1 min-h-0" style={{ minHeight: 320 }}>
        {loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-zinc-900/70">
            <Loader2 className="h-7 w-7 animate-spin text-violet-400" />
          </div>
        )}
        <div ref={mapContainer} className="w-full h-full rounded-t-xl" />
      </div>

      {/* Store info strip */}
      <div className="bg-zinc-900 border-t border-zinc-800 px-4 py-3 rounded-b-xl">
        {selected ? (
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-start gap-2 min-w-0">
              <MapPin className="h-4 w-4 text-violet-400 mt-0.5 flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-sm font-medium text-zinc-100 truncate">{selected.name}</p>
                <p className="text-xs text-zinc-500 truncate">{selected.address}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={`text-[10px] px-1.5 py-0 ${
                    selected.available_stock > 0
                      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                      : 'bg-red-500/15 text-red-400 border-red-500/30'
                  }`}>
                    <Package className="h-2.5 w-2.5 mr-1" />
                    {selected.available_stock > 0 ? `${selected.available_stock} items available` : 'Out of stock'}
                  </Badge>
                  {selected.distance_km && (
                    <span className="text-[10px] text-zinc-600 flex items-center gap-1">
                      <Navigation className="h-2.5 w-2.5" />
                      {selected.distance_km.toFixed(1)} km away
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <Button variant="outline" size="sm" onClick={() => setSelected(null)} className="text-xs border-zinc-700">
                Change
              </Button>
              <Button
                size="sm"
                onClick={handleConfirm}
                disabled={!selected.available_stock}
                className="text-xs bg-violet-600 hover:bg-violet-700"
              >
                Pick up here
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <MapPin className="h-4 w-4" />
            {loading ? 'Loading nearby stores…' : `${stores.length} stores found — click a pin to select`}
          </div>
        )}
      </div>
    </div>
  );
}
