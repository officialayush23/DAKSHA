// src/modules/super_admin/pages/CreateLocation.jsx

import React, { useState } from "react";
import api from "@/lib/apiClient"; // Use API Client
import { toast } from "sonner";
import { Loader2, Building, Warehouse, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LocationInput } from "./LocationInput";

export default function CreateLocation() {
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState("store"); 
  
  const [formData, setFormData] = useState({
    name: "",
    store_code: "", 
    city: "",
    address_line_1: "",
    latitude: "",
    longitude: ""
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        name: formData.name,
        type: type,
        city: formData.city,
        address_line_1: formData.address_line_1,
        latitude: formData.latitude ? parseFloat(formData.latitude) : 0,
        longitude: formData.longitude ? parseFloat(formData.longitude) : 0,
        // Map store_code to backend expectation
        store_code: type === 'store' ? formData.store_code : null,
        warehouse_code: type === 'warehouse' ? formData.store_code : null
      };

      // Call API
      await api.post("/admin/super/locations", payload);

      toast.success(`${type === 'store' ? 'Store' : 'Warehouse'} Created Successfully!`);
      
      // Reset
      setFormData({ name: "", store_code: "", city: "", address_line_1: "", latitude: "", longitude: "" });

    } catch (error) {
      console.error(error);
      toast.error("Failed to create location.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-bold text-white tracking-tight">Create Location</h2>
        <p className="text-zinc-400">Add a new fulfillment center to your network.</p>
      </div>

      <Card className="bg-zinc-950 border-zinc-800 text-white shadow-xl">
        <CardHeader className="border-b border-zinc-900 pb-6">
          <CardTitle className="text-lg font-medium flex items-center gap-2">
            <MapPin className="h-5 w-5 text-indigo-500" /> Location Details
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Type Switcher */}
            <div className="space-y-3">
              <Label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Location Type</Label>
              <div className="grid grid-cols-2 gap-4">
                <div 
                  onClick={() => setType("store")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-3 h-24 ${type === 'store' ? 'border-indigo-500 bg-indigo-500/10' : 'border-zinc-800 bg-zinc-900 hover:border-zinc-700'}`}
                >
                  <Building className={`h-6 w-6 ${type === 'store' ? 'text-indigo-400' : 'text-zinc-500'}`} />
                  <span className={`font-semibold text-sm ${type === 'store' ? 'text-white' : 'text-zinc-400'}`}>Retail Store</span>
                </div>
                <div 
                  onClick={() => setType("warehouse")}
                  className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-3 h-24 ${type === 'warehouse' ? 'border-emerald-500 bg-emerald-500/10' : 'border-zinc-800 bg-zinc-900 hover:border-zinc-700'}`}
                >
                  <Warehouse className={`h-6 w-6 ${type === 'warehouse' ? 'text-emerald-400' : 'text-zinc-500'}`} />
                  <span className={`font-semibold text-sm ${type === 'warehouse' ? 'text-white' : 'text-zinc-400'}`}>Warehouse</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>Name</Label>
                <Input placeholder="Location Name" className="bg-black border-zinc-800 h-11"
                  value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
              </div>
              <div className="space-y-2">
                <Label>Unique Code</Label>
                <Input placeholder="LOC-001" className="bg-black border-zinc-800 h-11 font-mono"
                  value={formData.store_code} onChange={e => setFormData({...formData, store_code: e.target.value})} required />
              </div>
            </div>

            <div className="space-y-2">
              <Label>City</Label>
              <Input placeholder="City Name" className="bg-black border-zinc-800 h-11"
                value={formData.city} onChange={e => setFormData({...formData, city: e.target.value})} required />
            </div>

            <div className="space-y-2">
              <Label>Full Address</Label>
              <Input placeholder="Address Line 1" className="bg-black border-zinc-800 h-11"
                value={formData.address_line_1} onChange={e => setFormData({...formData, address_line_1: e.target.value})} />
            </div>

            <LocationInput onDetect={({ latitude, longitude }) => setFormData({ ...formData, latitude: latitude.toString(), longitude: longitude.toString() })} />

            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>Latitude</Label>
                <Input type="number" className="bg-black border-zinc-800 h-11 font-mono"
                  value={formData.latitude} onChange={e => setFormData({...formData, latitude: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Longitude</Label>
                <Input type="number" className="bg-black border-zinc-800 h-11 font-mono"
                  value={formData.longitude} onChange={e => setFormData({...formData, longitude: e.target.value})} />
              </div>
            </div>

            <Button type="submit" className="w-full h-12 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-base rounded-xl mt-4" disabled={loading}>
              {loading ? <Loader2 className="animate-spin h-5 w-5 mr-2" /> : `Create ${type === 'store' ? 'Store' : 'Warehouse'}`}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}