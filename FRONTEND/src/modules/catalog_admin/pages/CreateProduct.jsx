import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Save, Loader2, Tag, DollarSign, Package, Info, ArrowLeft
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/apiClient"; // 1. Use API Client

// --- UI COMPONENTS ---
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function CreateProduct() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);

  // Form State matches database columns
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    base_price: "",
    category_id: "",
    gender: "unisex",
    season: "all_season", // Matches public.season_enum default
    usage_type: "casual",
    style_tags: "", 
  });

  // --- 1. FETCH CATEGORIES (Via API) ---
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const res = await api.get("/admin/catalog/categories");
        setCategories(res.data || []);
      } catch (err) {
        console.error("Fetch Error:", err);
        toast.error("Could not load categories.");
      }
    };
    loadCategories();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // --- 2. SUBMIT PRODUCT (Via API) ---
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.category_id) {
      toast.error("Please select a valid Category.");
      return;
    }

    setLoading(true);

    try {
      // Prepare Payload for Backend
      const payload = {
        name: formData.name,
        description: formData.description,
        category_id: formData.category_id,
        base_price: parseFloat(formData.base_price) || 0,
        gender: formData.gender,
        season: formData.season,
        usage_type: formData.usage_type,
        // Convert "tag1, tag2" string -> ["tag1", "tag2"] array for DB
        style_tags: formData.style_tags.split(",").map((tag) => tag.trim()).filter(t => t)
      };

      // Call API (POST /admin/catalog/products)
      const res = await api.post("/admin/catalog/products", payload);

      toast.success("Product created successfully!");
      
      // Navigate to Step 2: Create Variants using the new Product ID
      navigate(`/catalog/create-variant?product_id=${res.data.id}`);

    } catch (error) {
      console.error(error);
      toast.error("Failed to create product.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-zinc-800 animate-in fade-in">
      
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        
        {/* --- HEADER --- */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <div className="p-2 bg-zinc-900 rounded-lg border border-zinc-800">
                <Package className="h-6 w-6 text-white" />
              </div>
              New Product
            </h2>
            <p className="text-zinc-400 text-sm ml-1">
              Step 1 of 2: Define base product information.
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <Button 
              variant="ghost" 
              onClick={() => navigate("/catalog")} 
              className="text-zinc-400 hover:text-white hover:bg-zinc-900"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={loading} 
              className="bg-white text-black hover:bg-zinc-200 px-8 font-medium transition-transform active:scale-95"
            >
              {loading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...</>
              ) : (
                <><Save className="mr-2 h-4 w-4" /> Save & Continue</>
              )}
            </Button>
          </div>
        </div>

        {/* --- MAIN GRID --- */}
        <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT CONTENT (8 Cols) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* 1. General Info Card */}
            <Card className="bg-zinc-950 border-zinc-800 shadow-sm rounded-xl overflow-hidden">
              <div className="border-b border-zinc-900 bg-zinc-950/50 px-6 py-4">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">General Information</h3>
              </div>
              <CardContent className="p-6 space-y-6">
                
                <div className="space-y-2">
                  <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Product Name</Label>
                  <Input 
                    name="name" 
                    placeholder="e.g. Essential Oversized Tee" 
                    className="bg-black border-zinc-800 text-white h-10 focus-visible:ring-0 focus-visible:border-zinc-500 placeholder:text-zinc-600" 
                    value={formData.name} 
                    onChange={handleChange} 
                    required 
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Description</Label>
                  <Textarea 
                    name="description" 
                    placeholder="Describe the fabric, fit, and key features..." 
                    className="min-h-[140px] bg-black border-zinc-800 text-white focus-visible:ring-0 focus-visible:border-zinc-500 resize-y placeholder:text-zinc-600" 
                    value={formData.description} 
                    onChange={handleChange} 
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Category</Label>
                  <Select onValueChange={(val) => handleSelectChange("category_id", val)} value={formData.category_id}>
                    <SelectTrigger className="bg-black border-zinc-800 text-white h-10 focus:ring-0 focus:border-zinc-500">
                      <SelectValue placeholder="Select Category" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                      {categories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id} className="focus:bg-zinc-900 cursor-pointer">{cat.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

              </CardContent>
            </Card>

            {/* 2. Attributes Card */}
            <Card className="bg-zinc-950 border-zinc-800 shadow-sm rounded-xl overflow-hidden">
              <div className="border-b border-zinc-900 bg-zinc-950/50 px-6 py-4">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Attributes</h3>
              </div>
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Gender</Label>
                    <Select onValueChange={(val) => handleSelectChange("gender", val)} value={formData.gender}>
                      <SelectTrigger className="bg-black border-zinc-800 text-white h-10 focus:ring-0 focus:border-zinc-500"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                        {['men', 'women', 'kids', 'unisex'].map(g => (
                          <SelectItem key={g} value={g} className="capitalize focus:bg-zinc-900">{g}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Season</Label>
                    <Select onValueChange={(val) => handleSelectChange("season", val)} value={formData.season}>
                      <SelectTrigger className="bg-black border-zinc-800 text-white h-10 focus:ring-0 focus:border-zinc-500"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                        {['all_season', 'summer', 'winter', 'monsoon'].map(s => (
                          <SelectItem key={s} value={s} className="capitalize focus:bg-zinc-900">{s.replace('_', ' ')}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Usage</Label>
                    <Select onValueChange={(val) => handleSelectChange("usage_type", val)} value={formData.usage_type}>
                      <SelectTrigger className="bg-black border-zinc-800 text-white h-10 focus:ring-0 focus:border-zinc-500"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                        {['casual', 'formal', 'sportswear', 'party'].map(u => (
                          <SelectItem key={u} value={u} className="capitalize focus:bg-zinc-900">{u}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                </div>
              </CardContent>
            </Card>
          </div>

          {/* RIGHT SIDEBAR (4 Cols) */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Pricing Card */}
            <Card className="bg-zinc-950 border-zinc-800 shadow-sm rounded-xl overflow-hidden sticky top-6">
              <div className="border-b border-zinc-900 bg-zinc-950/50 px-6 py-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Pricing</h3>
                <Badge variant="outline" className="border-zinc-800 text-zinc-500">INR</Badge>
              </div>
              <CardContent className="p-6 space-y-6">
                
                <div className="space-y-2">
                  <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Base Price</Label>
                  <div className="relative">
                    <DollarSign className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                    <Input 
                      name="base_price" 
                      type="number" 
                      className="pl-9 bg-black border-zinc-800 text-white h-10 font-mono text-lg focus-visible:ring-0 focus-visible:border-emerald-500" 
                      placeholder="0.00"
                      value={formData.base_price} 
                      onChange={handleChange} 
                      required 
                    />
                  </div>
                </div>

                <div className="bg-zinc-900/50 border border-zinc-900 rounded-lg p-3 flex gap-3 items-start">
                  <Info className="h-4 w-4 text-zinc-500 mt-0.5 shrink-0" />
                  <p className="text-xs text-zinc-500 leading-relaxed">
                    Set the default price for this product. You can override this price for specific variants (e.g. XXL) in the next step.
                  </p>
                </div>

                <div className="space-y-2 pt-2">
                  <Label className="text-zinc-400 text-xs uppercase tracking-wide font-medium">Tags</Label>
                  <div className="relative">
                    <Tag className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                    <Input 
                      name="style_tags" 
                      className="pl-9 bg-black border-zinc-800 text-white h-10 focus-visible:ring-0 focus-visible:border-zinc-500" 
                      placeholder="Comma separated"
                      value={formData.style_tags} 
                      onChange={handleChange} 
                    />
                  </div>
                </div>

              </CardContent>
            </Card>

          </div>
        </form>
      </div>
    </div>
  );
}