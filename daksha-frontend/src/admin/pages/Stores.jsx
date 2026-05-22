// src/admin/pages/Stores.jsx
// Admin store management — Google Maps + Places autocomplete + geocoding
import React, { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogTrigger, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Card, CardHeader, CardTitle, CardContent, CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Plus, Store, MoreHorizontal, Search, Edit, Trash2, Download,
  Loader2, CheckCircle, XCircle, AlertCircle, Building, Globe,
  MapPin, RefreshCw, ShoppingBag, PackageCheck, Map, Crosshair,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

const API_BASE    = import.meta.env.VITE_API_URL || "http://localhost:8000";
const GMAPS_KEY   = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";

// ── Auth header helper ─────────────────────────────────────────────────────
const authHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token")}`,
});

// ── Load Google Maps once ─────────────────────────────────────────────────
let _gmapsLoaded = false, _gmapsCbs = [];
function loadGMaps() {
  return new Promise((r) => {
    if (window.google?.maps) { r(); return; }
    if (_gmapsLoaded) { _gmapsCbs.push(r); return; }
    _gmapsLoaded = true; _gmapsCbs.push(r);
    window.__gmapsAdminReady = () => _gmapsCbs.forEach(fn => fn());
    const s = document.createElement("script");
    s.src = `https://maps.googleapis.com/maps/api/js?key=${GMAPS_KEY}&libraries=places,geometry&callback=__gmapsAdminReady`;
    s.async = true; s.defer = true;
    document.head.appendChild(s);
  });
}

// ── API helpers ───────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(), ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// STORE PICKUPS DIALOG
// ─────────────────────────────────────────────────────────────────────────────
function StorePickupsDialog({ store, open, onOpenChange }) {
  const [pickups, setPickups] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !store) return;
    setLoading(true);
    apiFetch(`/admin/global/pickups`)
      .then(d => setPickups(Array.isArray(d) ? d.filter(p => p.store_id === store.id) : []))
      .catch(() => toast.error("Failed to load pickups"))
      .finally(() => setLoading(false));
  }, [open, store]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShoppingBag className="h-5 w-5" /> Pickups — {store?.name}
          </DialogTitle>
          <DialogDescription>Orders scheduled for pickup at this location</DialogDescription>
        </DialogHeader>
        <div className="border rounded-md min-h-[200px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Scheduled</TableHead>
                <TableHead className="text-right">Items</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={4} className="h-24 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                </TableCell></TableRow>
              ) : pickups.length === 0 ? (
                <TableRow><TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                  No pickups scheduled.
                </TableCell></TableRow>
              ) : pickups.map(p => (
                <TableRow key={p.id}>
                  <TableCell className="font-mono text-xs">{p.id?.slice(0, 8)}…</TableCell>
                  <TableCell><Badge variant="secondary">{p.status}</Badge></TableCell>
                  <TableCell className="text-sm">{p.scheduled_time ? new Date(p.scheduled_time).toLocaleString() : "—"}</TableCell>
                  <TableCell className="text-right">{p.items_count || 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ADDRESS AUTOCOMPLETE INPUT
// ─────────────────────────────────────────────────────────────────────────────
function AddressAutocomplete({ value, onChange, onPlaceSelect, placeholder }) {
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const sessionRef = useRef(crypto.randomUUID?.() || Math.random().toString(36));
  const debounceRef = useRef(null);

  const fetchSuggestions = useCallback(async (q) => {
    if (q.length < 3) { setSuggestions([]); setOpen(false); return; }
    setLoading(true);
    try {
      const params = new URLSearchParams({ q, session_token: sessionRef.current });
      const data = await apiFetch(`/stores/geocode/autocomplete?${params}`);
      setSuggestions(Array.isArray(data) ? data : []);
      setOpen(Array.isArray(data) && data.length > 0);
    } catch { /* silently ignore */ }
    finally { setLoading(false); }
  }, []);

  const handleChange = (e) => {
    onChange(e.target.value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(e.target.value), 280);
  };

  const handleSelect = async (suggestion) => {
    setOpen(false);
    onChange(suggestion.description);
    try {
      const data = await apiFetch("/stores/geocode/place", {
        method: "POST",
        body: JSON.stringify({ place_id: suggestion.place_id, session_token: sessionRef.current }),
      });
      // Rotate session token after a complete autocomplete session
      sessionRef.current = crypto.randomUUID?.() || Math.random().toString(36);
      onPlaceSelect(data);
    } catch (e) {
      toast.error("Could not resolve place: " + e.message);
    }
  };

  return (
    <div className="relative">
      <div className="relative">
        <Input
          value={value}
          onChange={handleChange}
          placeholder={placeholder || "Start typing an address…"}
          className="pr-8"
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onFocus={() => suggestions.length && setOpen(true)}
          autoComplete="off"
        />
        {loading && (
          <Loader2 className="absolute right-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 animate-spin text-muted-foreground" />
        )}
      </div>
      {open && (
        <ul className="absolute z-50 mt-1 w-full bg-popover border rounded-md shadow-lg text-sm overflow-hidden">
          {suggestions.map((s) => (
            <li
              key={s.place_id}
              onMouseDown={() => handleSelect(s)}
              className="flex items-start gap-2 px-3 py-2 cursor-pointer hover:bg-accent transition-colors"
            >
              <MapPin className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-muted-foreground" />
              <span className="text-xs leading-relaxed">{s.description}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MINI MAP (shows selected pin, draggable for fine-tuning)
// ─────────────────────────────────────────────────────────────────────────────
function MiniMap({ lat, lng, onDragEnd }) {
  const containerRef = useRef(null);
  const mapRef       = useRef(null);
  const markerRef    = useRef(null);
  const [gmapsReady, setGmapsReady] = useState(!!window.google?.maps);

  useEffect(() => {
    if (window.google?.maps) { setGmapsReady(true); return; }
    loadGMaps().then(() => setGmapsReady(true));
  }, []);

  useEffect(() => {
    if (!gmapsReady || !containerRef.current) return;
    if (!mapRef.current) {
      mapRef.current = new window.google.maps.Map(containerRef.current, {
        center: { lat: lat || 20.5937, lng: lng || 78.9629 },
        zoom: lat ? 15 : 5,
        mapTypeControl: false, streetViewControl: false,
        fullscreenControl: false, zoomControl: true,
        styles: [
          { featureType: "poi", stylers: [{ visibility: "off" }] },
          { featureType: "transit", stylers: [{ visibility: "off" }] },
        ],
      });
    }
    if (lat && lng) {
      const pos = { lat, lng };
      mapRef.current.panTo(pos);
      mapRef.current.setZoom(15);
      if (!markerRef.current) {
        markerRef.current = new window.google.maps.Marker({
          map: mapRef.current,
          position: pos,
          draggable: true,
          icon: {
            url: `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 44 44"><text y="38" font-size="36">🏪</text></svg>`,
            scaledSize: new window.google.maps.Size(44, 44),
            anchor: new window.google.maps.Point(22, 44),
          },
          title: "Store location — drag to fine-tune",
        });
        markerRef.current.addListener("dragend", (e) => {
          onDragEnd({ lat: e.latLng.lat(), lng: e.latLng.lng() });
        });
      } else {
        markerRef.current.setPosition(pos);
      }
    }
  }, [gmapsReady, lat, lng]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full rounded-lg"
      style={{ minHeight: "100%" }}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────────────────────
export default function StoresPage() {
  const [stores, setStores]         = useState([]);
  const [loading, setLoading]       = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedStore, setSelectedStore] = useState(null);
  const [isEditing, setIsEditing]   = useState(false);
  const [saving, setSaving]         = useState(false);

  const [isPickupsOpen, setIsPickupsOpen] = useState(false);
  const [pickupStore, setPickupStore] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    name: "", address: "", city: "", state: "", active: true,
    latitude: null, longitude: null,
  });
  const [geocoding, setGeocoding] = useState(false);

  // Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // ── Fetch stores ───────────────────────────────────────────────────────────
  const fetchStores = async () => {
    setLoading(true);
    try {
      const data = await apiFetch("/stores/admin/list");
      setStores(Array.isArray(data) ? data : []);
    } catch (e) {
      toast.error("Failed to load stores: " + e.message);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchStores(); }, []);

  // ── Handle place selection (autocomplete → geocoded) ───────────────────────
  const handlePlaceSelect = (placeData) => {
    setFormData(prev => ({
      ...prev,
      address: placeData.formatted_address || prev.address,
      city: placeData.city || prev.city,
      state: placeData.state || prev.state,
      latitude: placeData.lat,
      longitude: placeData.lng,
    }));
  };

  // ── Geocode manually typed address ─────────────────────────────────────────
  const handleManualGeocode = async () => {
    if (!formData.address) return;
    setGeocoding(true);
    try {
      const data = await apiFetch("/stores/geocode/address", {
        method: "POST",
        body: JSON.stringify({ address: formData.address }),
      });
      setFormData(prev => ({
        ...prev,
        latitude: data.lat,
        longitude: data.lng,
        city: prev.city || data.city || "",
        state: prev.state || data.state || "",
      }));
      toast.success("Address geocoded successfully");
    } catch (e) {
      toast.error("Geocoding failed: " + e.message);
    } finally { setGeocoding(false); }
  };

  // ── Submit create / update ─────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) { toast.error("Store name is required"); return; }
    if (!formData.address.trim()) { toast.error("Address is required"); return; }
    setSaving(true);
    try {
      const payload = {
        name: formData.name.trim(),
        address: formData.address.trim(),
        city: formData.city.trim(),
        state: formData.state.trim(),
        active: formData.active,
        latitude: formData.latitude,
        longitude: formData.longitude,
      };

      if (isEditing && selectedStore) {
        await apiFetch(`/stores/admin/${selectedStore.id}`, {
          method: "PUT", body: JSON.stringify(payload),
        });
        toast.success("Store updated");
      } else {
        await apiFetch("/stores/admin/create", {
          method: "POST", body: JSON.stringify(payload),
        });
        toast.success("Store created");
      }
      resetForm();
      setIsDialogOpen(false);
      fetchStores();
    } catch (e) {
      toast.error(e.message);
    } finally { setSaving(false); }
  };

  const handleEdit = (store) => {
    setSelectedStore(store);
    setIsEditing(true);
    setFormData({
      name: store.name || "",
      address: store.address || "",
      city: store.city || "",
      state: store.state || "",
      active: store.active !== false,
      latitude: store.latitude,
      longitude: store.longitude,
    });
    setIsDialogOpen(true);
  };

  const handleDeactivate = async (store) => {
    if (!window.confirm(`Deactivate "${store.name}"?`)) return;
    try {
      await apiFetch(`/stores/admin/${store.id}`, { method: "DELETE" });
      toast.success("Store deactivated");
      fetchStores();
    } catch (e) { toast.error(e.message); }
  };

  const resetForm = () => {
    setFormData({ name: "", address: "", city: "", state: "", active: true, latitude: null, longitude: null });
    setSelectedStore(null);
    setIsEditing(false);
  };

  // ── Filters ────────────────────────────────────────────────────────────────
  const filtered = stores.filter(s => {
    const q = searchQuery.toLowerCase();
    const matchSearch = !q || s.name?.toLowerCase().includes(q) || s.city?.toLowerCase().includes(q) || s.address?.toLowerCase().includes(q);
    const matchStatus = statusFilter === "all" || (statusFilter === "active" && s.active !== false) || (statusFilter === "inactive" && s.active === false);
    return matchSearch && matchStatus;
  });

  const activeCount = stores.filter(s => s.active !== false).length;
  const stateCount  = new Set(stores.map(s => s.state).filter(Boolean)).size;

  const exportCSV = () => {
    const rows = [
      ["Name", "City", "State", "Address", "Status", "Latitude", "Longitude"],
      ...filtered.map(s => [s.name, s.city || "", s.state || "", s.address || "", s.active !== false ? "Active" : "Inactive", s.latitude || "", s.longitude || ""]),
    ].map(r => r.join(",")).join("\n");
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob([rows], { type: "text/csv" })), download: `stores_${Date.now()}.csv` });
    a.click();
    toast.success("Exported");
  };

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="p-6 space-y-6">
      <StorePickupsDialog store={pickupStore} open={isPickupsOpen} onOpenChange={setIsPickupsOpen} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Store Management</h1>
          <p className="text-muted-foreground">Manage physical store locations — powered by Google Maps</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={exportCSV} className="gap-2">
            <Download className="w-4 h-4" /> Export
          </Button>
          <Button variant="outline" size="sm" onClick={fetchStores} disabled={loading} className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>

          <Dialog open={isDialogOpen} onOpenChange={(v) => { setIsDialogOpen(v); if (!v) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="gap-2"><Plus className="w-4 h-4" /> Add Store</Button>
            </DialogTrigger>

            <DialogContent className="max-w-4xl max-h-[92vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{isEditing ? "Edit Store" : "Register New Store"}</DialogTitle>
                <DialogDescription>
                  {isEditing ? "Update store details — address is re-geocoded automatically." : "Type an address to auto-detect lat/lng via Google Maps."}
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* LEFT: Form fields */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Store Name *</Label>
                      <Input
                        placeholder="e.g. Mumbai Central Store"
                        value={formData.name}
                        onChange={e => setFormData(p => ({ ...p, name: e.target.value }))}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Address * (with Google Places autocomplete)</Label>
                      <AddressAutocomplete
                        value={formData.address}
                        onChange={v => setFormData(p => ({ ...p, address: v }))}
                        onPlaceSelect={handlePlaceSelect}
                        placeholder="Start typing a store address…"
                      />
                      {formData.address && !formData.latitude && (
                        <Button
                          type="button" variant="outline" size="sm"
                          onClick={handleManualGeocode}
                          disabled={geocoding}
                          className="gap-2 text-xs mt-1"
                        >
                          {geocoding ? <Loader2 className="h-3 w-3 animate-spin" /> : <Crosshair className="h-3 w-3" />}
                          {geocoding ? "Geocoding…" : "Geocode this address"}
                        </Button>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>City</Label>
                        <Input placeholder="e.g. Mumbai" value={formData.city} onChange={e => setFormData(p => ({ ...p, city: e.target.value }))} />
                      </div>
                      <div className="space-y-2">
                        <Label>State</Label>
                        <Input placeholder="e.g. Maharashtra" value={formData.state} onChange={e => setFormData(p => ({ ...p, state: e.target.value }))} />
                      </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                      <div>
                        <Label>Active</Label>
                        <p className="text-xs text-muted-foreground">Make this store available for pickup orders</p>
                      </div>
                      <Switch checked={formData.active} onCheckedChange={v => setFormData(p => ({ ...p, active: v }))} />
                    </div>

                    {/* Coordinates display */}
                    <div className="p-3 bg-muted/40 rounded-lg space-y-2">
                      <Label className="flex items-center gap-1.5 text-xs font-semibold">
                        <MapPin className="h-3.5 w-3.5 text-violet-500" />
                        Resolved Coordinates
                      </Label>
                      {formData.latitude ? (
                        <div className="grid grid-cols-2 gap-2">
                          <div className="font-mono text-xs bg-background rounded p-2">
                            Lat: {formData.latitude.toFixed(6)}
                          </div>
                          <div className="font-mono text-xs bg-background rounded p-2">
                            Lng: {formData.longitude.toFixed(6)}
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">
                          Select an address from autocomplete or click "Geocode this address"
                        </p>
                      )}
                    </div>
                  </div>

                  {/* RIGHT: Mini map */}
                  <div className="space-y-2">
                    <Label className="flex items-center gap-1.5">
                      <Map className="h-4 w-4" /> Live Map Preview
                    </Label>
                    <div className="h-[380px] border rounded-lg overflow-hidden">
                      <MiniMap
                        lat={formData.latitude}
                        lng={formData.longitude}
                        onDragEnd={({ lat, lng }) =>
                          setFormData(p => ({ ...p, latitude: lat, longitude: lng }))
                        }
                      />
                    </div>
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        Drag the 🏪 marker to fine-tune the store's exact location on the map.
                      </AlertDescription>
                    </Alert>
                  </div>
                </div>

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                  <Button type="submit" disabled={saving} className="gap-2">
                    {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                    {isEditing ? "Update Store" : "Create Store"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: "Total Stores", value: stores.length, sub: `${activeCount} active`, icon: Store },
          { label: "Active Stores", value: activeCount, sub: `${((activeCount / (stores.length || 1)) * 100).toFixed(0)}% active rate`, icon: CheckCircle },
          { label: "States Covered", value: stateCount, sub: `${new Set(stores.map(s => s.city).filter(Boolean)).size} cities`, icon: Globe },
        ].map(({ label, value, sub, icon: Icon }) => (
          <Card key={label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{label}</CardTitle>
              <Icon className="w-5 h-5 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{value}</div>
              <p className="text-sm text-muted-foreground mt-1">{sub}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex items-center gap-2 flex-1">
            <Search className="w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by name, city, or address…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="max-w-sm"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Stores</SelectItem>
              <SelectItem value="active">Active Only</SelectItem>
              <SelectItem value="inactive">Inactive Only</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Store Locations</CardTitle>
          <CardDescription>{filtered.length} store{filtered.length !== 1 ? "s" : ""} found</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Store</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Coordinates</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell colSpan={5} className="text-center py-10">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                  </TableCell></TableRow>
                ) : filtered.length === 0 ? (
                  <TableRow><TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
                    <Store className="w-10 h-10 mx-auto mb-2 opacity-40" />
                    <p className="font-medium">No stores found</p>
                    <p className="text-sm">Add a new store to get started</p>
                  </TableCell></TableRow>
                ) : filtered.map((store) => (
                  <TableRow key={store.id} className="hover:bg-muted/50">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-full bg-violet-100 dark:bg-violet-900/30 text-lg">🏪</div>
                        <div>
                          <div className="font-medium">{store.name}</div>
                          <div className="text-xs text-muted-foreground font-mono">{store.id?.slice(0, 8)}…</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-start gap-1">
                        <MapPin className="h-3.5 w-3.5 mt-0.5 text-violet-500 flex-shrink-0" />
                        <div>
                          <div className="font-medium text-sm">{store.city || "—"}{store.state ? `, ${store.state}` : ""}</div>
                          <div className="text-xs text-muted-foreground line-clamp-1 max-w-[200px]">{store.address || "—"}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {store.latitude ? (
                        <div className="font-mono text-xs text-muted-foreground space-y-0.5">
                          <div>{store.latitude?.toFixed(5)}</div>
                          <div>{store.longitude?.toFixed(5)}</div>
                        </div>
                      ) : <span className="text-xs text-muted-foreground">Not set</span>}
                    </TableCell>
                    <TableCell>
                      <Badge variant={store.active !== false ? "default" : "secondary"} className="gap-1">
                        {store.active !== false
                          ? <><CheckCircle className="w-3 h-3" /> Active</>
                          : <><XCircle className="w-3 h-3" /> Inactive</>}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => handleEdit(store)}>
                            <Edit className="mr-2 h-4 w-4" /> Edit Store
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => { setPickupStore(store); setIsPickupsOpen(true); }}>
                            <PackageCheck className="mr-2 h-4 w-4" /> View Pickups
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-destructive" onClick={() => handleDeactivate(store)}>
                            <Trash2 className="mr-2 h-4 w-4" /> Deactivate
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
