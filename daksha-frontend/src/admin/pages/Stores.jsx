import React, { useState, useEffect } from "react";
import { AdminService } from '@/lib/adminApi';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import {
  Badge
} from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  Plus, 
  Store, 
  MoreHorizontal, 
  Search,
  Edit,
  Trash2,
  Download,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Building,
  Map,
  Globe,
  Pin,
  MapPin,
  RefreshCw,
  ShoppingBag,
  PackageCheck
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

// Leaflet imports
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for Leaflet default icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Icons
const createCustomIcon = () => {
  return new L.DivIcon({
    html: `
      <div style="
        position: relative;
        width: 40px;
        height: 40px;
        background: #3b82f6;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
      </div>
    `,
    className: 'custom-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
  });
};

const createActiveStoreIcon = () => {
  return new L.DivIcon({
    html: `
      <div style="
        position: relative;
        width: 40px;
        height: 40px;
        background: #10b981;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
      </div>
    `,
    className: 'active-store-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
  });
};

const createInactiveStoreIcon = () => {
  return new L.DivIcon({
    html: `
      <div style="
        position: relative;
        width: 40px;
        height: 40px;
        background: #ef4444;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.7;
      ">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
          <circle cx="12" cy="10" r="3"/>
        </svg>
      </div>
    `,
    className: 'inactive-store-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -40]
  });
};

// Helper function to parse location
const parseLocation = (location) => {
  if (!location) return { type: 'Point', coordinates: [73.8677, 18.4650] };
  
  if (typeof location === 'string') {
    try {
      return JSON.parse(location);
    } catch (e) {
      console.error('Failed to parse location string:', e);
      return { type: 'Point', coordinates: [73.8677, 18.4650] };
    }
  }
  
  return location;
};

// Helper function to get coordinates
const getCoordinates = (location) => {
  const parsed = parseLocation(location);
  if (parsed.coordinates && Array.isArray(parsed.coordinates) && parsed.coordinates.length >= 2) {
    // Note: In GeoJSON, coordinates are [longitude, latitude]
    // For Leaflet, we need [latitude, longitude]
    return [parsed.coordinates[1], parsed.coordinates[0]];
  }
  return [18.4650, 73.8677]; // Default to Pune
};

// Location Picker Component
function LocationPicker({ onLocationSelect, initialPosition }) {
  const [position, setPosition] = useState(initialPosition || [18.4650, 73.8677]);
  
  const map = useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng;
      setPosition([lat, lng]);
      // Convert to GeoJSON format: [longitude, latitude]
      onLocationSelect({ type: 'Point', coordinates: [lng, lat] });
    },
    locationfound: (e) => {
      const { lat, lng } = e.latlng;
      setPosition([lat, lng]);
      onLocationSelect({ type: 'Point', coordinates: [lng, lat] });
      map.flyTo([lat, lng], map.getZoom());
    },
  });

  useEffect(() => {
    map.locate();
  }, [map]);

  return position ? (
    <Marker 
      position={position} 
      icon={createCustomIcon()}
      eventHandlers={{
        dragend: (e) => {
          const marker = e.target;
          const position = marker.getLatLng();
          setPosition([position.lat, position.lng]);
          // Convert to GeoJSON format: [longitude, latitude]
          onLocationSelect({ type: 'Point', coordinates: [position.lng, position.lat] });
        },
      }}
      draggable={true}
    >
      <Popup>
        <div className="p-2">
          <h3 className="font-bold">Selected Location</h3>
          <p className="text-sm">Click and drag to adjust position</p>
          <p className="text-xs font-mono mt-1">
            Lat: {position[0].toFixed(6)}, Lng: {position[1].toFixed(6)}
          </p>
        </div>
      </Popup>
    </Marker>
  ) : null;
}

// --- NEW COMPONENT: Store Pickups Dialog ---
const StorePickupsDialog = ({ store, open, onOpenChange }) => {
  const [pickups, setPickups] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && store) {
      fetchPickups();
    }
  }, [open, store]);

  const fetchPickups = async () => {
    setLoading(true);
    try {
      const data = await AdminService.listStorePickups(store.id);
      setPickups(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching pickups:", error);
      toast.error("Failed to load pickups");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShoppingBag className="h-5 w-5" />
            Pickups for {store?.name}
          </DialogTitle>
          <DialogDescription>List of orders scheduled for pickup at this location</DialogDescription>
        </DialogHeader>

        <div className="border rounded-md min-h-[200px]">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order ID</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Items</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                  </TableCell>
                </TableRow>
              ) : pickups.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                    No pickups scheduled for this store.
                  </TableCell>
                </TableRow>
              ) : (
                pickups.map((pickup) => (
                  <TableRow key={pickup.id}>
                    <TableCell className="font-mono text-xs">{pickup.id.slice(0,8)}...</TableCell>
                    <TableCell>{pickup.customer_name || 'N/A'}</TableCell>
                    <TableCell>
                      <Badge variant={pickup.status === 'completed' ? 'default' : 'secondary'}>
                        {pickup.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{pickup.items_count || 0}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Main Component
export default function StoresPage() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedStore, setSelectedStore] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  
  // Pickups Dialog State
  const [isPickupsOpen, setIsPickupsOpen] = useState(false);
  const [pickupStore, setPickupStore] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    city: "",
    state: "",
    address: "",
    active: true,
    location: {
      type: "Point",
      coordinates: [73.8677, 18.4650] // [longitude, latitude]
    }
  });

  // Map State
  const [mapPosition, setMapPosition] = useState([18.4650, 73.8677]); // [latitude, longitude]
  const [mapZoom, setMapZoom] = useState(12);
  
  // Filter States
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [stateFilter, setStateFilter] = useState("all");

  // 1. Fetch Stores
  const fetchStores = async () => {
    try {
      setLoading(true);
      const data = await AdminService.listStores();
      const storesList = Array.isArray(data) ? data : [];
      setStores(storesList);
      toast.success("Stores loaded successfully");
    } catch (err) {
      console.error("Failed to fetch stores", err);
      toast.error("Failed to load stores");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, []);

  // 2. Handle Form Submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Prepare the data in correct format
      const storeData = {
        name: formData.name.trim(),
        city: formData.city.trim(),
        state: formData.state.trim(),
        address: formData.address.trim(),
        location: formData.location, // Already in correct GeoJSON format
        active: formData.active
      };

      if (isEditing && selectedStore) {
        await AdminService.updateStore(selectedStore.id, storeData);
        toast.success("Store updated successfully");
      } else {
        await AdminService.createStore(storeData);
        toast.success("Store created successfully");
      }
      
      resetForm();
      setIsDialogOpen(false);
      fetchStores();
    } catch (err) {
      console.error("Error saving store:", err);
      // Extract better error message
      let errorMessage = "Failed to save store";
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map(e => e.msg).join(", ");
        } else {
          errorMessage = err.response.data.detail;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      toast.error(errorMessage);
    }
  };

  // 3. Handle Edit Store
  const handleEdit = (store) => {
    setSelectedStore(store);
    setIsEditing(true);
    
    const parsedLocation = parseLocation(store.location);
    const coordinates = parsedLocation.coordinates || [73.8677, 18.4650];
    
    setFormData({
      name: store.name || "",
      city: store.city || "",
      state: store.state || "",
      address: store.address || "",
      active: store.active !== false,
      location: parsedLocation
    });
    
    // Set map position (convert from [lng, lat] to [lat, lng])
    setMapPosition([coordinates[1], coordinates[0]]);
    setIsDialogOpen(true);
  };

  // 4. Reset Form
  const resetForm = () => {
    setFormData({
      name: "",
      city: "",
      state: "",
      address: "",
      active: true,
      location: {
        type: "Point",
        coordinates: [73.8677, 18.4650]
      }
    });
    setSelectedStore(null);
    setIsEditing(false);
    setMapPosition([18.4650, 73.8677]);
  };

  // 5. Handle Location Selection
  const handleLocationSelect = (location) => {
    setFormData(prev => ({
      ...prev,
      location
    }));
  };

  // 6. Filter Stores
  const filteredStores = stores.filter(store => {
    const matchesSearch = 
      store.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      store.city?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      store.address?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = 
      statusFilter === "all" || 
      (statusFilter === "active" && store.active !== false) ||
      (statusFilter === "inactive" && store.active === false);
    
    const matchesState = 
      stateFilter === "all" || 
      store.state === stateFilter;
    
    return matchesSearch && matchesStatus && matchesState;
  });

  // 7. Calculate Statistics
  const activeStores = stores.filter(store => store.active !== false).length;
  const statesCovered = new Set(stores.map(s => s.state).filter(Boolean)).size;
  const citiesCovered = new Set(stores.map(s => s.city).filter(Boolean)).size;

  // 8. Get Store Icon
  const getStoreIcon = (store) => {
    return store.active !== false ? createActiveStoreIcon() : createInactiveStoreIcon();
  };

  // 9. Export Stores
  const exportStores = () => {
    const csvContent = [
      ['Store Name', 'City', 'State', 'Address', 'Status', 'Longitude', 'Latitude'],
      ...filteredStores.map(store => {
        const parsedLocation = parseLocation(store.location);
        const coordinates = parsedLocation.coordinates || [0, 0];
        return [
          store.name,
          store.city || '',
          store.state || '',
          store.address || '',
          store.active !== false ? 'Active' : 'Inactive',
          coordinates[0] || '', // longitude
          coordinates[1] || ''  // latitude
        ];
      })
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stores_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    
    toast.success("Stores exported successfully");
  };

  // 10. Handle Delete Store (Deactivate instead)
  const handleDeleteStore = async (store) => {
    if (window.confirm("Are you sure you want to deactivate this store?")) {
      try {
        // Get the current store data to preserve all fields
        const parsedLocation = parseLocation(store.location);
        
        // Prepare update data with ALL required fields
        const updateData = {
          name: store.name || "",
          city: store.city || "",
          state: store.state || "",
          address: store.address || "",
          active: false,
          location: parsedLocation // Include the full location object
        };
        
        console.log("Deactivating store with data:", updateData);
        
        await AdminService.updateStore(store.id, updateData);
        toast.success("Store deactivated successfully");
        fetchStores();
      } catch (error) {
        console.error("Failed to deactivate store:", error);
        console.dir(error); // Log the full error object
        
        // Extract better error message
        let errorMessage = "Failed to deactivate store";
        
        if (error.response?.data?.detail) {
          if (Array.isArray(error.response.data.detail)) {
            errorMessage = error.response.data.detail.map(err => err.msg).join(", ");
          } else {
            errorMessage = error.response.data.detail;
          }
        } else if (error.response?.data?.message) {
          errorMessage = error.response.data.message;
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        toast.error(errorMessage);
      }
    }
  };

  // New: Open Pickups Dialog
  const handleViewPickups = (store) => {
    setPickupStore(store);
    setIsPickupsOpen(true);
  };

  // Get unique states from stores
  const storeStates = Array.from(new Set(stores.map(s => s.state).filter(Boolean)));

  return (
    <div className="p-6 space-y-6">
      {/* Pickups Dialog */}
      <StorePickupsDialog 
        store={pickupStore} 
        open={isPickupsOpen} 
        onOpenChange={setIsPickupsOpen} 
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Store Management</h1>
          <p className="text-muted-foreground">
            Manage physical store locations
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={exportStores} className="gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={fetchStores} disabled={loading} className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={(open) => {
            setIsDialogOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button className="gap-2">
                <Plus className="w-4 h-4" /> Add Store
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  {isEditing ? "Edit Store" : "Register New Store"}
                </DialogTitle>
                <DialogDescription>
                  {isEditing 
                    ? "Update store details and location" 
                    : "Add a new physical store location"}
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Column: Form Fields */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Store Name *</Label>
                      <Input 
                        id="name"
                        placeholder="e.g. Mumbai Main Store"
                        value={formData.name}
                        onChange={(e) => setFormData({...formData, name: e.target.value})}
                        required
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="city">City *</Label>
                        <Input 
                          id="city"
                          placeholder="e.g. Mumbai"
                          value={formData.city}
                          onChange={(e) => setFormData({...formData, city: e.target.value})}
                          required
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="state">State *</Label>
                        <Input 
                          id="state"
                          placeholder="e.g. Maharashtra"
                          value={formData.state}
                          onChange={(e) => setFormData({...formData, state: e.target.value})}
                          required
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="address">Complete Address *</Label>
                      <Textarea 
                        id="address"
                        placeholder="Enter full address..."
                        value={formData.address}
                        onChange={(e) => setFormData({...formData, address: e.target.value})}
                        rows={3}
                        required
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Active Status</Label>
                        <p className="text-sm text-muted-foreground">Make this store operational</p>
                      </div>
                      <Switch 
                        checked={formData.active}
                        onCheckedChange={(checked) => setFormData({...formData, active: checked})}
                      />
                    </div>
                    
                    {/* Coordinates Display */}
                    <div className="space-y-2 p-3 bg-muted rounded-lg">
                      <Label className="flex items-center gap-2">
                        <Pin className="w-4 h-4" />
                        Selected Coordinates (GeoJSON)
                      </Label>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="font-mono bg-background p-2 rounded">
                          Longitude: {formData.location.coordinates[0].toFixed(6)}
                        </div>
                        <div className="font-mono bg-background p-2 rounded">
                          Latitude: {formData.location.coordinates[1].toFixed(6)}
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Format: [longitude, latitude]
                      </p>
                    </div>
                  </div>
                  
                  {/* Right Column: Map */}
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Map className="w-4 h-4" />
                      Select Location on Map
                    </Label>
                    
                    <div className="h-[400px] border rounded-lg overflow-hidden">
                      <MapContainer
                        center={mapPosition}
                        zoom={mapZoom}
                        className="h-full w-full"
                        style={{ height: '100%', width: '100%' }}
                      >
                        <TileLayer
                          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                        <LocationPicker 
                          onLocationSelect={handleLocationSelect}
                          initialPosition={mapPosition}
                        />
                      </MapContainer>
                    </div>
                    
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        Click on the map to set the exact store location. Drag the marker to fine-tune.
                      </AlertDescription>
                    </Alert>
                  </div>
                </div>
                
                <DialogFooter>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setIsDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">
                    {isEditing ? "Update Store" : "Create Store"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Total Stores
            </CardTitle>
            <Store className="w-5 h-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {stores.length}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {activeStores} active
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Active Stores
            </CardTitle>
            <CheckCircle className="w-5 h-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {activeStores}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {((activeStores / stores.length) * 100 || 0).toFixed(1)}% active rate
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">
              Coverage
            </CardTitle>
            <Globe className="w-5 h-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {statesCovered}
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {citiesCovered} cities
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 flex-1">
              <Search className="w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search stores by name, city, or address..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="max-w-sm"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Stores</SelectItem>
                  <SelectItem value="active">Active Only</SelectItem>
                  <SelectItem value="inactive">Inactive Only</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={stateFilter} onValueChange={setStateFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="State" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All States</SelectItem>
                  {storeStates.map(state => (
                    <SelectItem key={state} value={state}>{state}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stores Table */}
      <Card>
        <CardHeader>
          <CardTitle>Store Locations</CardTitle>
          <CardDescription>
            {filteredStores.length} store{filteredStores.length !== 1 ? 's' : ''} found
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[300px]">Store Details</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-10">
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading stores...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : filteredStores.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-10 text-muted-foreground">
                      <Store className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p className="font-medium">No stores found</p>
                      <p className="text-sm">Try adjusting your search or add a new store</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredStores.map((store) => {
                    const parsedLocation = parseLocation(store.location);
                    const coordinates = parsedLocation.coordinates || [0, 0];
                    
                    return (
                      <TableRow key={store.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/30">
                              <Building className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div>
                              <div className="font-medium">{store.name}</div>
                              <div className="text-sm text-muted-foreground">
                                ID: {store.id?.slice(0, 8) || 'N/A'}...
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium flex items-center gap-1">
                              <MapPin className="w-3 h-3" />
                              {store.city || 'Unknown City'}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {store.state || 'Unknown State'}
                            </div>
                            <div className="text-xs font-mono text-muted-foreground mt-1">
                              {coordinates[0]?.toFixed(4) || 'N/A'}, {coordinates[1]?.toFixed(4) || 'N/A'}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={store.active !== false ? "default" : "secondary"}
                            className="gap-1"
                          >
                            {store.active !== false ? (
                              <>
                                <CheckCircle className="w-3 h-3" />
                                Active
                              </>
                            ) : (
                              <>
                                <XCircle className="w-3 h-3" />
                                Inactive
                              </>
                            )}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Store Actions</DropdownMenuLabel>
                              <DropdownMenuItem onClick={() => handleEdit(store)}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit Store
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleViewPickups(store)}>
                                <PackageCheck className="mr-2 h-4 w-4" />
                                View Pickups
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-destructive"
                                onClick={() => handleDeleteStore(store)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Deactivate Store
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Map Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Store Locations Map
          </CardTitle>
          <CardDescription>
            Visual overview of all store locations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] rounded-lg overflow-hidden border">
            <MapContainer
              center={[20.5937, 78.9629]} // Center of India
              zoom={4}
              className="h-full w-full"
              style={{ height: '400px', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {stores.map(store => {
                if (!store.location) return null;
                const coordinates = getCoordinates(store.location);
                return (
                  <Marker 
                    key={store.id} 
                    position={coordinates}
                    icon={getStoreIcon(store)}
                  >
                    <Popup>
                      <div className="p-2">
                        <h3 className="font-bold">{store.name}</h3>
                        <p className="text-sm">{store.city}, {store.state}</p>
                        <p className="text-xs text-muted-foreground">{store.address}</p>
                        <div className="mt-2">
                          <Badge variant={store.active !== false ? "default" : "secondary"}>
                            {store.active !== false ? "Active" : "Inactive"}
                          </Badge>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
            </MapContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}