// src/modules/catalog_admin/pages/CategoryManager.jsx

import React, { useState, useEffect } from "react";
import { 
  Plus, FolderTree, Search, LayoutGrid, Loader2
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/apiClient"; // 1. Use API Client

// --- UI COMPONENTS ---
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

export default function CategoryManager() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [newCat, setNewCat] = useState({
    name: "",
    slug: "",
    parent_id: "none"
  });

  // --- FETCH DATA ---
  const fetchCategories = async () => {
    setLoading(true);
    try {
      // Call Backend API
      const res = await api.get("/admin/catalog/categories");
      setCategories(res.data || []);
    } catch (error) {
      console.error("Fetch Error:", error);
      toast.error("Failed to load categories.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  // --- HANDLE SUBMIT ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newCat.name || !newCat.slug) return;

    setSubmitting(true);
    try {
      const payload = {
        name: newCat.name,
        slug: newCat.slug,
        // Convert "none" string back to null for API
        parent_id: newCat.parent_id === "none" ? null : newCat.parent_id
      };

      // Call Backend API
      await api.post("/admin/catalog/categories", payload);

      toast.success("Category created successfully");
      
      // Refresh List
      fetchCategories(); 
      setNewCat({ name: "", slug: "", parent_id: "none" });

    } catch (error) {
      console.error("Create Error:", error);
      toast.error(error.response?.data?.detail || "Failed to create category.");
    } finally {
      setSubmitting(false);
    }
  };

  // Auto-generate slug logic
  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === "name" && !newCat.slug) {
      const autoSlug = value.toLowerCase().replace(/ /g, "-").replace(/[^\w-]+/g, "");
      setNewCat(prev => ({ ...prev, name: value, slug: autoSlug }));
    } else {
      setNewCat(prev => ({ ...prev, [name]: value }));
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-8 space-y-8 font-sans animate-in fade-in">
      
      {/* --- PAGE HEADER --- */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-zinc-900">
        <div className="space-y-1">
          <h2 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <LayoutGrid className="h-8 w-8 text-zinc-500" />
            Category Structure
          </h2>
          <p className="text-zinc-400 text-sm max-w-lg">
            Organize your global catalog into a hierarchy.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        
        {/* --- LEFT: CREATE FORM --- */}
        <Card className="lg:col-span-1 bg-zinc-950 border-zinc-800 shadow-xl sticky top-6">
          <CardHeader className="bg-zinc-900/30 border-b border-zinc-800/50 pb-4">
            <CardTitle className="flex items-center gap-2 text-white text-lg">
              <Plus className="h-5 w-5 text-emerald-500" /> 
              Create New
            </CardTitle>
            <CardDescription className="text-zinc-500 text-xs">
              Add a new node to the category tree.
            </CardDescription>
          </CardHeader>
          
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-5">
              
              {/* Name Input */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Display Name
                </Label>
                <Input 
                  name="name" 
                  placeholder="e.g. Winter Collection" 
                  className="bg-black border-zinc-800 text-white focus:border-emerald-500/50 transition-all h-10" 
                  value={newCat.name} 
                  onChange={handleChange} 
                  required 
                />
              </div>

              {/* Slug Input */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    URL Slug
                  </Label>
                  <span className="text-[10px] text-zinc-600 font-mono">auto-generated</span>
                </div>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-zinc-600">/</span>
                  <Input 
                    name="slug" 
                    placeholder="winter-collection" 
                    className="pl-6 bg-black border-zinc-800 text-zinc-300 font-mono text-sm focus:border-emerald-500/50 transition-all h-10" 
                    value={newCat.slug} 
                    onChange={handleChange} 
                    required 
                  />
                </div>
              </div>

              {/* Parent Select */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Parent Category
                </Label>
                <Select 
                  value={newCat.parent_id} 
                  onValueChange={(val) => setNewCat(prev => ({ ...prev, parent_id: val }))}
                >
                  <SelectTrigger className="bg-black border-zinc-800 text-white h-10">
                    <SelectValue placeholder="No Parent (Top Level)" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                    <SelectItem value="none" className="text-zinc-400">No Parent (Top Level)</SelectItem>
                    <Separator className="bg-zinc-800 my-1" />
                    {categories.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id} className="focus:bg-zinc-900 cursor-pointer">
                        {cat.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="pt-2">
                <Button 
                  type="submit" 
                  className="w-full bg-white text-black hover:bg-zinc-200 h-10 font-medium transition-transform active:scale-[0.98]" 
                  disabled={submitting}
                >
                  {submitting ? (
                    <span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin"/> Saving...</span>
                  ) : (
                    "Create Category"
                  )}
                </Button>
              </div>

            </form>
          </CardContent>
        </Card>

        {/* --- RIGHT: LIST VIEW --- */}
        <Card className="lg:col-span-2 bg-zinc-950 border-zinc-800 shadow-none">
          <CardHeader className="flex flex-row items-center justify-between border-b border-zinc-800 py-4 px-6">
            <div className="flex items-center gap-2">
              <FolderTree className="h-5 w-5 text-zinc-400" />
              <CardTitle className="text-white text-base">Current Taxonomy</CardTitle>
            </div>
            <div className="relative hidden md:block w-64">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-zinc-500" />
              <Input 
                placeholder="Filter categories..." 
                className="h-8 pl-8 bg-black border-zinc-800 text-xs text-white placeholder:text-zinc-600" 
              />
            </div>
          </CardHeader>
          
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-zinc-900/50">
                <TableRow className="border-zinc-800 hover:bg-transparent">
                  <TableHead className="text-zinc-500 font-medium h-10 w-[40%] pl-6">Category Name</TableHead>
                  <TableHead className="text-zinc-500 font-medium h-10">Slug</TableHead>
                  <TableHead className="text-zinc-500 font-medium h-10 text-right pr-6">Level</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  [1, 2, 3].map((i) => (
                    <TableRow key={i} className="border-zinc-800">
                      <TableCell className="pl-6"><Skeleton className="h-4 w-32 bg-zinc-900" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24 bg-zinc-900" /></TableCell>
                      <TableCell className="pr-6"><Skeleton className="h-4 w-12 bg-zinc-900 ml-auto" /></TableCell>
                    </TableRow>
                  ))
                ) : categories.length === 0 ? (
                  <TableRow className="border-zinc-800 hover:bg-transparent">
                    <TableCell colSpan={3} className="h-48 text-center">
                      <div className="flex flex-col items-center justify-center text-zinc-500 gap-2">
                        <FolderTree className="h-8 w-8 opacity-20" />
                        <p>No categories defined yet.</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  categories.map((cat) => (
                    <TableRow key={cat.id} className="border-zinc-800 hover:bg-zinc-900/50 group transition-colors">
                      <TableCell className="font-medium text-white py-4 pl-6">
                        <div className="flex items-center gap-2">
                          {cat.parent_id ? (
                            <div className="flex items-center text-zinc-600">
                              <span className="w-4 h-[1px] bg-zinc-700 mr-2"></span>
                              <span className="text-sm text-zinc-300">{cat.name}</span>
                            </div>
                          ) : (
                            <span className="text-sm font-semibold">{cat.name}</span>
                          )}
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-[10px] text-zinc-400 border-zinc-700 bg-zinc-900/50 px-2 py-0.5">
                          {cat.slug}
                        </Badge>
                      </TableCell>
                      
                      <TableCell className="text-right pr-6">
                        {cat.parent_id ? (
                          <span className="text-xs text-zinc-500">Sub-category</span>
                        ) : (
                          <span className="text-xs text-emerald-500 font-medium bg-emerald-950/20 px-2 py-1 rounded">Root</span>
                        )}
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
  );
}