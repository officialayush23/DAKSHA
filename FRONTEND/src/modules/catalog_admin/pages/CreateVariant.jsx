
import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { 
  ArrowLeft, Plus, Trash2, UploadCloud, Loader2, Image as ImageIcon, Search, Copy, Check, Package, AlertCircle
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/apiClient"; 
import { supabase } from '@/lib/supabaseClient'; 

// --- UI COMPONENTS ---
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function CreateVariant() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const productId = searchParams.get("product_id");

  // State
  const [manualIdInput, setManualIdInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const [product, setProduct] = useState(null);
  const [variants, setVariants] = useState([]);

  // Form State - NOW INCLUDES ALL DB FIELDS
  const [newVariant, setNewVariant] = useState({
    sku: "",
    size_label: "", 
    color_name: "", 
    color_hex: "#000000",
    material: "",
    pattern: "",
    fit_type: "",
    price_override: "", 
    image_url: ""
  });

  // --- 1. FETCH DATA ---
  useEffect(() => {
    if (!productId) {
      setProduct(null);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const [prodRes, varRes] = await Promise.all([
          api.get(`/admin/catalog/products/${productId}`),
          api.get(`/admin/catalog/products/${productId}/variants`)
        ]);

        setProduct(prodRes.data);
        setVariants(varRes.data || []);

      } catch (error) {
        console.error("Error loading data:", error);
        toast.error("Product not found or access denied.");
        setProduct(null);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [productId]);

  // --- HANDLERS ---
  const handleManualIdSubmit = (e) => {
    e.preventDefault();
    if (manualIdInput.trim()) setSearchParams({ product_id: manualIdInput.trim() });
  };

  const copyIdToClipboard = () => {
    if (productId) {
      navigator.clipboard.writeText(productId);
      setCopied(true);
      toast.success("ID copied!");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const fileExt = file.name.split('.').pop();
      const filePath = `${productId}/${Date.now()}.${fileExt}`;
      
      const { error: uploadError } = await supabase.storage.from('product-images').upload(filePath, file);
      if (uploadError) throw uploadError;

      const { data } = supabase.storage.from('product-images').getPublicUrl(filePath);
      setNewVariant(prev => ({ ...prev, image_url: data.publicUrl }));
      toast.success("Image uploaded!");
    } catch (error) {
      toast.error("Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleAddVariant = async (e) => {
    e.preventDefault();
    if (!newVariant.sku || !newVariant.size_label || !newVariant.color_name) {
      return toast.error("SKU, Size, and Color are required.");
    }

    setSubmitting(true);
    try {
      const payload = {
        product_id: productId,
        sku: newVariant.sku,
        size_label: newVariant.size_label,
        color_name: newVariant.color_name,
        color_hex: newVariant.color_hex,
        material: newVariant.material || null,
        pattern: newVariant.pattern || null,
        fit_type: newVariant.fit_type || null,
        image_url: newVariant.image_url || null,
        price_override: newVariant.price_override ? parseFloat(newVariant.price_override) : null,
      };

      const res = await api.post("/admin/catalog/variants", payload);

      toast.success("Variant added!");
      setVariants([res.data, ...variants]);
      // Reset form (keep some helpers if needed)
      setNewVariant({ 
        sku: "", size_label: "", color_name: "", color_hex: "#000000", 
        material: "", pattern: "", fit_type: "", price_override: "", image_url: "" 
      });

    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to add variant.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteVariant = async (variantId) => {
    if (!confirm("Delete this variant?")) return;
    try {
      await api.delete(`/admin/catalog/variants/${variantId}`);
      setVariants(variants.filter(v => v.id !== variantId));
      toast.success("Deleted.");
    } catch (error) {
      toast.error("Delete failed.");
    }
  };

  if (!productId || (!loading && !product)) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
        <Card className="w-full max-w-md bg-zinc-950 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Search className="h-5 w-5 text-zinc-400" /> Load Product
            </CardTitle>
            <CardDescription className="text-zinc-500">Enter Product UUID.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleManualIdSubmit} className="space-y-4">
              <Input placeholder="e.g. 123e4567-..." className="bg-black border-zinc-800 text-white"
                value={manualIdInput} onChange={(e) => setManualIdInput(e.target.value)} />
              <Button type="submit" disabled={!manualIdInput} className="w-full bg-white text-black hover:bg-zinc-200">Continue</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-white">
        <Loader2 className="h-6 w-6 animate-spin mr-3 text-zinc-500" /> 
        <span className="text-zinc-400 text-sm tracking-wide">SYNCING CATALOG...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white font-sans flex justify-center py-10 px-6 animate-in fade-in">
      <div className="w-full max-w-7xl space-y-8">
        
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-2">
          <div className="flex items-center gap-5">
            <Button variant="outline" size="icon" onClick={() => navigate("/catalog")} className="h-10 w-10 rounded-full border-zinc-800 bg-black text-zinc-400 hover:bg-zinc-900 hover:text-white">
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold tracking-tight text-white">{product.name}</h1>
                <Badge variant="outline" className="border-zinc-800 text-zinc-500 text-[10px] uppercase tracking-wider bg-zinc-900/50">
                  {product.categories?.name}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <span className="font-mono bg-zinc-900 px-1.5 py-0.5 rounded cursor-pointer" onClick={copyIdToClipboard}>
                  {productId.slice(0, 8)}... {copied && <Check className="inline h-3 w-3 text-emerald-500" />}
                </span>
                <span>•</span>
                <span>Base: <span className="text-white">₹{product.base_price}</span></span>
              </div>
            </div>
          </div>
          <Button variant="secondary" onClick={() => navigate("/catalog/list")} className="bg-zinc-900 text-white hover:bg-zinc-800 border border-zinc-800 h-10 px-6">
            Done
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* LEFT: FORM (4 Cols) */}
          <Card className="lg:col-span-4 bg-zinc-950 border-zinc-800 shadow-sm overflow-hidden sticky top-6">
            <div className="border-b border-zinc-900 bg-zinc-950/50 px-5 py-4 flex items-center gap-2">
              <Plus className="h-4 w-4 text-emerald-500" />
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Add New Variant</h3>
            </div>
            <CardContent className="p-5 space-y-5">
              <form onSubmit={handleAddVariant} className="space-y-5">
                
                {/* Image Upload */}
                <label className="group flex flex-col items-center justify-center w-full h-32 border border-dashed border-zinc-800 rounded-lg cursor-pointer bg-black hover:bg-zinc-900 hover:border-zinc-600 transition-all overflow-hidden relative">
                  {newVariant.image_url ? (
                    <img src={newVariant.image_url} alt="Preview" className="h-full w-full object-contain p-2" />
                  ) : (
                    <div className="flex flex-col items-center justify-center pt-5 pb-6 text-zinc-600 group-hover:text-zinc-400">
                        {uploading ? <Loader2 className="h-6 w-6 animate-spin" /> : <UploadCloud className="h-8 w-8 mb-2" />}
                        <p className="text-[10px] uppercase tracking-wide">Click to Upload</p>
                    </div>
                  )}
                  <input type="file" className="hidden" accept="image/*" onChange={handleImageUpload} disabled={uploading} />
                </label>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-xs">SKU *</Label>
                    <Input placeholder="Unique ID" className="bg-black border-zinc-800 text-white h-9"
                      value={newVariant.sku} onChange={(e) => setNewVariant({...newVariant, sku: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-xs">Size *</Label>
                    <Input placeholder="XL, 42, etc" className="bg-black border-zinc-800 text-white h-9"
                      value={newVariant.size_label} onChange={(e) => setNewVariant({...newVariant, size_label: e.target.value})} />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-400 text-xs">Color *</Label>
                  <div className="flex gap-2">
                    <Input type="color" className="w-12 h-9 p-1 bg-black border-zinc-800 cursor-pointer"
                      value={newVariant.color_hex} onChange={(e) => setNewVariant({...newVariant, color_hex: e.target.value})} />
                    <Input placeholder="Color Name" className="bg-black border-zinc-800 text-white h-9"
                      value={newVariant.color_name} onChange={(e) => setNewVariant({...newVariant, color_name: e.target.value})} />
                  </div>
                </div>

                {/* --- NEW FIELDS --- */}
                <div className="space-y-2">
                  <Label className="text-zinc-400 text-xs">Material</Label>
                  <Input placeholder="Cotton, Polyester..." className="bg-black border-zinc-800 text-white h-9"
                    value={newVariant.material} onChange={(e) => setNewVariant({...newVariant, material: e.target.value})} />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-xs">Pattern</Label>
                    <Select onValueChange={(val) => setNewVariant({...newVariant, pattern: val})} value={newVariant.pattern}>
                        <SelectTrigger className="bg-black border-zinc-800 h-9"><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                            {["Solid", "Striped", "Checked", "Printed", "Textured"].map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}
                        </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-xs">Fit Type</Label>
                    <Select onValueChange={(val) => setNewVariant({...newVariant, fit_type: val})} value={newVariant.fit_type}>
                        <SelectTrigger className="bg-black border-zinc-800 h-9"><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                            {["Regular", "Slim", "Oversized", "Loose", "Skinny"].map(f => <SelectItem key={f} value={f}>{f}</SelectItem>)}
                        </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-zinc-400 text-xs">Price Override</Label>
                  <Input type="number" placeholder={`Base: ₹${product.base_price}`} className="bg-black border-zinc-800 text-white h-9"
                    value={newVariant.price_override} onChange={(e) => setNewVariant({...newVariant, price_override: e.target.value})} />
                </div>

                <Button type="submit" className="w-full bg-white text-black hover:bg-zinc-200 h-10 font-medium" disabled={submitting || uploading}>
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin"/> : <Plus className="h-4 w-4 mr-2"/>} Add Variant
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* RIGHT: LIST (8 Cols) */}
          <Card className="lg:col-span-8 bg-zinc-950 border-zinc-800 shadow-sm overflow-hidden min-h-[500px]">
             <div className="border-b border-zinc-900 bg-zinc-950/50 px-6 py-4 flex items-center justify-between">
               <div className="flex items-center gap-2">
                 <Package className="h-4 w-4 text-zinc-400" />
                 <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Inventory List</h3>
               </div>
               <Badge variant="secondary" className="bg-zinc-900 text-zinc-400">{variants.length} items</Badge>
             </div>
             <CardContent className="p-0">
               <Table>
                 <TableHeader className="bg-zinc-900/50">
                   <TableRow className="border-zinc-800 hover:bg-transparent">
                     <TableHead className="text-zinc-500 h-10 text-center">Img</TableHead>
                     <TableHead className="text-zinc-500 h-10">Details</TableHead>
                     <TableHead className="text-zinc-500 h-10">Specs</TableHead>
                     <TableHead className="text-zinc-500 h-10">Price</TableHead>
                     <TableHead className="text-zinc-500 h-10 text-right pr-6">Action</TableHead>
                   </TableRow>
                 </TableHeader>
                 <TableBody>
                   {variants.length === 0 ? (
                     <TableRow className="border-zinc-800 hover:bg-transparent">
                       <TableCell colSpan={5} className="h-64 text-center text-zinc-500">No variants.</TableCell>
                     </TableRow>
                   ) : (
                     variants.map((v) => (
                       <TableRow key={v.id} className="border-zinc-800 hover:bg-zinc-900/40 group transition-colors">
                         <TableCell className="text-center py-4">
                           <div className="h-10 w-10 rounded-md bg-black border border-zinc-800 overflow-hidden inline-flex items-center justify-center">
                             {v.image_url ? <img src={v.image_url} className="h-full w-full object-cover"/> : <ImageIcon className="h-4 w-4 text-zinc-700"/>}
                           </div>
                         </TableCell>
                         <TableCell className="py-4">
                           <div className="flex flex-col">
                             <span className="font-mono text-xs text-white">{v.sku}</span>
                             <div className="flex items-center gap-2 mt-1">
                               <span className="text-[10px] bg-zinc-900 px-1 rounded text-zinc-400">{v.size_label}</span>
                               <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                                 <div className="w-2 h-2 rounded-full" style={{backgroundColor: v.color_hex}}></div>
                                 {v.color_name}
                               </span>
                             </div>
                           </div>
                         </TableCell>
                         <TableCell className="py-4 text-xs text-zinc-400">
                            <div>{v.material || '-'}</div>
                            <div>{v.fit_type} {v.pattern ? `• ${v.pattern}` : ''}</div>
                         </TableCell>
                         <TableCell className="py-4">
                           {v.price_override ? <span className="text-emerald-400 text-sm">₹{v.price_override}</span> : <span className="text-zinc-500 text-sm">₹{product.base_price}</span>}
                         </TableCell>
                         <TableCell className="text-right pr-6 py-4">
                           <Button variant="ghost" size="icon" className="h-8 w-8 text-zinc-500 hover:text-red-400" onClick={() => handleDeleteVariant(v.id)}>
                             <Trash2 className="h-4 w-4" />
                           </Button>
                         </TableCell>
                       </TableRow>
                     ))
                   )}
                 </TableBody>
               </Table>
             </CardContent>
           </Card>

        </div>
      </div>
    </div>
  );
}
