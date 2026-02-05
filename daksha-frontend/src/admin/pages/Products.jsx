import React, { useEffect, useState } from 'react';
import { AdminService } from '@/lib/adminApi';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Plus,
  MoreHorizontal,
  Loader2,
  Search,
  Package,
  Palette,
  ChevronRight,
  ChevronDown,
  Edit,
  Trash2,
  Image as ImageIcon,
  Copy,
  RefreshCw,
  Grid3x3,
  List,
  Upload,
  X,
  Warehouse,
  Globe,
  Boxes,
  Store,
  Eye,
  CheckCircle2
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);
  const [variants, setVariants] = useState({});
  const [loading, setLoading] = useState(true);
  const [variantsLoading, setVariantsLoading] = useState({});
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [viewMode, setViewMode] = useState("list");

  // Real API Inventory Stats
  const [inventoryStats, setInventoryStats] = useState({
    total_variants_tracked: 0,
    total_global_stock: 0,
    stock_at_stores: 0,
    stock_in_warehouse: 0
  });

  // Dialog States
  const [isProductDialogOpen, setIsProductDialogOpen] = useState(false);
  const [isVariantDialogOpen, setIsVariantDialogOpen] = useState(false);
  const [isImageDialogOpen, setIsImageDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isInventoryDialogOpen, setIsInventoryDialogOpen] = useState(false);
  const [isViewInventoryOpen, setIsViewInventoryOpen] = useState(false); // NEW
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Expanded products for tree view
  const [expandedProducts, setExpandedProducts] = useState({});

  // Current item being edited/deleted
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingVariant, setEditingVariant] = useState(null);
  const [deletingItem, setDeletingItem] = useState({ type: '', id: '', name: '' });
  const [currentVariant, setCurrentVariant] = useState(null);

  // Inventory Manage State
  const [inventoryType, setInventoryType] = useState('global');
  const [inventoryForm, setInventoryForm] = useState({ store_id: "", quantity: "" });

  // Inventory View State (NEW)
  const [viewInventoryData, setViewInventoryData] = useState(null);
  const [viewStoreId, setViewStoreId] = useState("");
  const [viewStoreData, setViewStoreData] = useState(null);
  const [viewLoading, setViewLoading] = useState(false);

  // Image upload state
  const [uploadingImage, setUploadingImage] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const GENDER_OPTIONS = [
    { value: "male", label: "Male" }, { value: "female", label: "Female" },
    { value: "unisex", label: "Unisex" }, { value: "kids", label: "Kids" }
  ];
  const CATEGORIES = ["Shoes", "Clothing", "Accessories", "Bags", "Jewelry", "Watches", "Eyewear", "Fragrances", "Skincare", "Home"];
  const SIZES = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"];
  const COLORS = ["Black", "White", "Red", "Blue", "Green", "Yellow", "Purple", "Pink", "Orange", "Brown"];

  const [productForm, setProductForm] = useState({ brand: "", category: "", gender: "", fabric_type: "", description: "", occasion: "", active: true });
  const [variantForm, setVariantForm] = useState({ product_id: "", sku: "", color: "", size: "", base_price: "", active: true });
  const [imageForm, setImageForm] = useState({ position: 0 });

  const categories = Array.from(new Set(products.map(p => p.category).filter(Boolean)));

  const fetchData = async () => {
    setLoading(true);
    try {
      const [productsData, storesData, kpisData] = await Promise.all([
        AdminService.listProducts(),
        AdminService.listStores(),
        AdminService.getInventoryKpis()
      ]);
      setProducts(Array.isArray(productsData) ? productsData : []);
      setStores(Array.isArray(storesData) ? storesData : storesData.data || []);
      setInventoryStats(kpisData || { total_variants_tracked: 0, total_global_stock: 0, stock_at_stores: 0, stock_in_warehouse: 0 });
      toast.success("Dashboard data loaded");
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const fetchVariants = async (productId) => {
    try {
      setVariantsLoading(prev => ({ ...prev, [productId]: true }));
      const variantsList = await AdminService.listVariants(productId);
      setVariants(prev => ({ ...prev, [productId]: Array.isArray(variantsList) ? variantsList : [] }));
    } catch (error) {
      console.error(`Failed to fetch variants`, error);
      setVariants(prev => ({ ...prev, [productId]: [] }));
    } finally {
      setVariantsLoading(prev => ({ ...prev, [productId]: false }));
    }
  };

  // --- CRUD Operations (Abbreviated for clarity - same as previous) ---
  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const cleanFormData = {
        name: productForm.name.trim(), // <--- Include Name
        brand: productForm.brand.trim(),
        category: productForm.category.trim(),
        gender: productForm.gender.trim(),
        fabric_type: productForm.fabric_type.trim(),
        description: productForm.description.trim(),
        occasion: productForm.occasion.trim()
      };

      await AdminService.createProduct(cleanFormData);
      toast.success("Product created"); resetProductForm(); setIsProductDialogOpen(false); fetchData();
    } catch (error) { toast.error("Failed"); } finally { setIsSubmitting(false); }
  };
  const handleUpdateProduct = async (e) => {
    e.preventDefault(); if (!editingProduct) return; setIsSubmitting(true);
    try {
      await AdminService.updateProduct(editingProduct.id, productForm);
      toast.success("Updated"); resetProductForm(); setEditingProduct(null); setIsProductDialogOpen(false); fetchData();
    } catch (error) { toast.error("Failed"); } finally { setIsSubmitting(false); }
  };
  const handleDeleteProduct = async () => {
    if (!deletingItem.id) return; setIsSubmitting(true);
    try {
      await AdminService.deleteProduct(deletingItem.id);
      toast.success("Deleted"); setIsDeleteDialogOpen(false); setDeletingItem({ type: '', id: '', name: '' }); fetchData();
    } catch (error) { toast.error("Failed"); } finally { setIsSubmitting(false); }
  };
  const handleCreateVariant = async (e) => {
    e.preventDefault(); setIsSubmitting(true);
    try {
      await AdminService.createVariant({ ...variantForm, base_price: parseFloat(variantForm.base_price) || 0 });
      toast.success("Created"); resetVariantForm(); setIsVariantDialogOpen(false); if (variantForm.product_id) fetchVariants(variantForm.product_id);
    } catch (error) { toast.error("Failed"); } finally { setIsSubmitting(false); }
  };
  const handleUpdateVariant = async (e) => {
    e.preventDefault(); if (!editingVariant) return; setIsSubmitting(true);
    try {
      await AdminService.updateVariant(editingVariant.id, { ...variantForm, base_price: parseFloat(variantForm.base_price) || 0 });
      toast.success("Updated"); resetVariantForm(); setEditingVariant(null); setIsVariantDialogOpen(false); if (variantForm.product_id) fetchVariants(variantForm.product_id);
    } catch (error) { toast.error("Failed"); } finally { setIsSubmitting(false); }
  };
  const handleDeleteVariant = async () => {
    if (!deletingItem.id) return; setIsSubmitting(true);
    try {
      await AdminService.deleteVariant(deletingItem.id);
      toast.success("Deleted"); setIsDeleteDialogOpen(false); setDeletingItem({ type: '', id: '', name: '' });
      const v = variants[deletingItem.productId]?.find(v => v.id === deletingItem.id); if (v) fetchVariants(v.product_id);
    } catch (error) { toast.error("Failed"); } finally { setIsSubmitting(false); }
  };

  // --- Inventory Management (MANAGE) ---
  const openInventoryDialog = (variant, type) => {
    setCurrentVariant(variant);
    setInventoryType(type);
    setInventoryForm({ store_id: "", quantity: "" });
    setIsInventoryDialogOpen(true);
  };

  const handleInventorySubmit = async (e) => {
    e.preventDefault(); setIsSubmitting(true);
    try {
      const quantity = parseInt(inventoryForm.quantity);
      if (isNaN(quantity) || quantity < 0) throw new Error("Invalid quantity");
      if (inventoryType === 'global') {
        await AdminService.assignGlobalInventory({ product_variant_id: currentVariant.id, quantity });
        toast.success(`Global inventory updated`);
      } else {
        if (!inventoryForm.store_id) throw new Error("Please select a store");
        await AdminService.assignStoreInventory({ store_id: inventoryForm.store_id, product_variant_id: currentVariant.id, quantity });
        toast.success(`Store inventory updated`);
      }
      setInventoryStats(await AdminService.getInventoryKpis());
      setIsInventoryDialogOpen(false);
    } catch (error) { toast.error(error.message); } finally { setIsSubmitting(false); }
  };

  // --- Inventory View (VIEW) ---
  const openViewInventory = async (variant) => {
    setCurrentVariant(variant);
    setViewInventoryData(null);
    setViewStoreData(null);
    setViewStoreId("");
    setIsViewInventoryOpen(true);
    setViewLoading(true);

    try {
      // 1. Fetch Global Inventory List for this Product (Parent)
      // The API returns a list of all variants' inventory for the product
      const globalList = await AdminService.getGlobalInventoryItem(variant.product_id);

      // 2. Find THIS specific variant in the list
      const thisVariantData = Array.isArray(globalList)
        ? globalList.find(item => item.product_variant_id === variant.id)
        : null;

      setViewInventoryData(thisVariantData);
    } catch (error) {
      console.error("Error viewing inventory", error);
      toast.error("Failed to fetch global inventory");
    } finally {
      setViewLoading(false);
    }
  };

  const handleViewStoreInventory = async (storeId) => {
    setViewStoreId(storeId);
    if (!storeId) {
      setViewStoreData(null);
      return;
    }

    try {
      const res = await AdminService.getStoreInventoryForVariant(
        storeId,
        currentVariant.id
      );

      setViewStoreData(res);
    } catch (error) {
      console.error("Error fetching store inventory", error);
      setViewStoreData({
        message: "No stock found for this variant in the selected store",
      });
    }
  };


  // --- Image Upload ---
  const handleImageUpload = async (e) => {
    e.preventDefault(); if (!currentVariant || !imageFile) return; setUploadingImage(true);
    try {
      const formData = new FormData(); formData.append('file', imageFile);
      const res = await fetch(
        `http://localhost:8000/admin/variants/${currentVariant.id}/images`,
        {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`,
          },
        }
      );

      if (!res.ok) throw new Error("Upload failed");
      const { image_url } = await res.json();
      await AdminService.addImage(currentVariant.id, { image_url, position: parseInt(imageForm.position) || 0 });
      toast.success("Image added"); resetImageForm(); setIsImageDialogOpen(false); if (currentVariant.product_id) fetchVariants(currentVariant.product_id);
    } catch (error) { toast.error("Failed"); } finally { setUploadingImage(false); }
  };
  const handleFileChange = (e) => {
    const file = e.target.files[0]; if (!file) return;
    if (!file.type.startsWith('image/')) return toast.error('Images only');
    setImageFile(file); const reader = new FileReader(); reader.onloadend = () => setImagePreview(reader.result); reader.readAsDataURL(file);
  };

  // --- Helpers ---
  const toggleProductExpansion = async (pid) => {
    const isExpanded = expandedProducts[pid]; setExpandedProducts(prev => ({ ...prev, [pid]: !isExpanded }));
    if (!isExpanded && !variants[pid]) await fetchVariants(pid);
  };
  const resetProductForm = () => setProductForm({ name: "", brand: "", category: "", gender: "", fabric_type: "", description: "", occasion: "", active: true });
  const resetVariantForm = () => setVariantForm({ product_id: "", sku: "", color: "", size: "", base_price: "", active: true });
  const resetImageForm = () => { setImageForm({ position: 0 }); setImageFile(null); setImagePreview(null); setCurrentVariant(null); };
  const openEditProductDialog = (p) => {
    setEditingProduct(p);
    setProductForm({
      name: p.name || "", // <--- Load Name
      brand: p.brand || "",
      category: p.category || "",
      gender: p.gender || "",
      fabric_type: p.fabric_type || "",
      description: p.description || "",
      occasion: p.occasion || "",
      active: p.active !== false
    });
    setIsProductDialogOpen(true);
  };
  const openEditVariantDialog = (v, pid) => { setEditingVariant(v); setVariantForm({ ...v, product_id: pid, active: v.active !== false }); setIsVariantDialogOpen(true); };
  const openAddImageDialog = (v) => { setCurrentVariant(v); setIsImageDialogOpen(true); };
  const openDeleteDialog = (type, id, name, pid = null) => { setDeletingItem({ type, id, name, productId: pid }); setIsDeleteDialogOpen(true); };

  useEffect(() => { fetchData(); }, []);

  const filteredProducts = products.filter(p => {
    const matchesSearch = p.brand?.toLowerCase().includes(searchTerm.toLowerCase()) || p.category?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = filterCategory === "all" || p.category === filterCategory;
    const matchesStatus = filterStatus === "all" || (filterStatus === "active" ? p.active !== false : p.active === false);
    return matchesSearch && matchesCategory && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header & Stats (Same as before) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div><h1 className="text-3xl font-bold tracking-tight">Products & Inventory</h1><p className="text-muted-foreground">Manage catalog and stock</p></div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}><RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />Refresh</Button>
          <Button onClick={() => setIsProductDialogOpen(true)}><Plus className="mr-2 h-4 w-4" /> Add Product</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Global Stock</CardTitle><Globe className="h-4 w-4 text-blue-600" /></CardHeader><CardContent><div className="text-2xl font-bold">{inventoryStats.total_global_stock}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Warehouse</CardTitle><Boxes className="h-4 w-4 text-amber-600" /></CardHeader><CardContent><div className="text-2xl font-bold">{inventoryStats.stock_in_warehouse}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Store Stock</CardTitle><Store className="h-4 w-4 text-green-600" /></CardHeader><CardContent><div className="text-2xl font-bold">{inventoryStats.stock_at_stores}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Active SKUs</CardTitle><Palette className="h-4 w-4 text-purple-600" /></CardHeader><CardContent><div className="text-2xl font-bold">{inventoryStats.total_variants_tracked}</div></CardContent></Card>
      </div>

      {/* List View */}
      <div className="rounded-md border bg-card">
        {loading ? <div className="h-64 flex items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div> : (
          <div className="divide-y">
            {filteredProducts.map((product) => {
              const isExpanded = expandedProducts[product.id];
              const productVariants = variants[product.id] || [];
              return (
                <Collapsible key={product.id} open={isExpanded} onOpenChange={() => toggleProductExpansion(product.id)}>
                  <div className="p-4 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <CollapsibleTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">{isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}</Button>
                        </CollapsibleTrigger>
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/30"><Package className="h-4 w-4 text-blue-600" /></div>
                          <div>
                            <div className="flex items-center gap-2"><h3 className="font-medium">{product.brand}</h3><span className="text-muted-foreground">•</span><span className="text-primary font-medium">{product.category}</span></div>
                            <p className="text-sm text-muted-foreground">{product.description}</p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-medium hidden md:inline">{productVariants.length} variants</span>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild><Button variant="ghost" className="h-8 w-8 p-0"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEditProductDialog(product)}><Edit className="mr-2 h-4 w-4" /> Edit</DropdownMenuItem>
                            <DropdownMenuItem onClick={() => { setVariantForm(prev => ({ ...prev, product_id: product.id })); setIsVariantDialogOpen(true); }}><Plus className="mr-2 h-4 w-4" /> Add Variant</DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive" onClick={() => openDeleteDialog('product', product.id, product.brand)}><Trash2 className="mr-2 h-4 w-4" /> Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </div>
                  <CollapsibleContent>
                    <div className="px-4 pb-4">
                      <div className="border rounded-lg bg-muted/30">
                        {variantsLoading[product.id] ? <div className="h-24 flex items-center justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div> : (
                          <Table>
                            <TableHeader><TableRow className="bg-muted/50"><TableHead>SKU</TableHead><TableHead>Color</TableHead><TableHead>Size</TableHead><TableHead>Price</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
                            <TableBody>
                              {productVariants.map(variant => (
                                <TableRow key={variant.id}>
                                  <TableCell className="font-mono text-xs">{variant.sku}</TableCell>
                                  <TableCell><div className="flex items-center gap-2">{variant.color && <div className="h-3 w-3 rounded-full border" style={{ backgroundColor: variant.color.toLowerCase() }} />}<span>{variant.color}</span></div></TableCell>
                                  <TableCell>{variant.size && <Badge variant="outline">{variant.size}</Badge>}</TableCell>
                                  <TableCell>₹{variant.base_price}</TableCell>
                                  <TableCell className="text-right">
                                    <DropdownMenu>
                                      <DropdownMenuTrigger asChild><Button variant="ghost" size="sm" className="h-8 w-8 p-0"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
                                      <DropdownMenuContent align="end">
                                        <DropdownMenuLabel>View</DropdownMenuLabel>
                                        <DropdownMenuItem onClick={() => openViewInventory(variant)}>
                                          <Eye className="mr-2 h-4 w-4" /> View Inventory
                                        </DropdownMenuItem>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuLabel>Manage</DropdownMenuLabel>
                                        <DropdownMenuItem onClick={() => openInventoryDialog(variant, 'global')}><Globe className="mr-2 h-4 w-4" /> Global Inv</DropdownMenuItem>
                                        <DropdownMenuItem onClick={() => openInventoryDialog(variant, 'store')}><Warehouse className="mr-2 h-4 w-4" /> Store Inv</DropdownMenuItem>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuItem onClick={() => openEditVariantDialog(variant, product.id)}><Edit className="mr-2 h-4 w-4" /> Edit</DropdownMenuItem>
                                        <DropdownMenuItem onClick={() => openAddImageDialog(variant)}><ImageIcon className="mr-2 h-4 w-4" /> Images</DropdownMenuItem>
                                        <DropdownMenuItem className="text-destructive" onClick={() => openDeleteDialog('variant', variant.id, variant.sku, product.id)}><Trash2 className="mr-2 h-4 w-4" /> Delete</DropdownMenuItem>
                                      </DropdownMenuContent>
                                    </DropdownMenu>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              );
            })}
          </div>
        )}
      </div>

      {/* --- INVENTORY VIEW DIALOG --- */}
      <Dialog open={isViewInventoryOpen} onOpenChange={setIsViewInventoryOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Inventory Status</DialogTitle>
            <DialogDescription>
              Viewing stock for SKU: <span className="font-mono text-primary font-bold">{currentVariant?.sku}</span>
            </DialogDescription>
          </DialogHeader>

          {viewLoading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin" /></div>
          ) : (
            <div className="space-y-6 py-4">
              {/* Global Section */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2"><Globe className="h-4 w-4 text-blue-500" /> Global Overview</h4>
                {viewInventoryData ? (
                  <div className="grid grid-cols-3 gap-2 text-center bg-muted/50 p-3 rounded-lg border">
                    <div>
                      <div className="text-2xl font-bold">{viewInventoryData.total_stock || 0}</div>
                      <div className="text-xs text-muted-foreground">Total Stock</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-amber-600">{viewInventoryData.reserved_stock || 0}</div>
                      <div className="text-xs text-muted-foreground">Reserved</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">{viewInventoryData.assigned_stock || 0}</div>
                      <div className="text-xs text-muted-foreground">Assigned</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground text-center p-4 border rounded-lg bg-muted/30">
                    No global inventory record found.
                  </div>
                )}
              </div>

              <div className="border-t" />

              {/* Store Section */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium flex items-center gap-2"><Store className="h-4 w-4 text-green-600" /> Check Store Stock</h4>
                <div className="flex gap-2">
                  <Select value={viewStoreId} onValueChange={handleViewStoreInventory}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a store to check..." />
                    </SelectTrigger>
                    <SelectContent>
                      {stores.map(store => (
                        <SelectItem key={store.id} value={store.id}>{store.name} ({store.city})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {viewStoreId && (
                  <div className="bg-muted/30 p-4 rounded-lg border mt-2">
                    {viewStoreData ? (
                      viewStoreData.message ? (
                        <div className="text-sm text-muted-foreground text-center">{viewStoreData.message}</div>
                      ) : (
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-medium">Available Stock</div>
                            <div className="text-xs text-muted-foreground">At selected location</div>
                          </div>
                          <div className="text-3xl font-bold text-primary">
                            {viewStoreData.available}
                          </div>

                        </div>
                      )
                    ) : (
                      <div className="text-sm text-muted-foreground text-center">Loading store data...</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setIsViewInventoryOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* --- INVENTORY MANAGE DIALOG --- */}
      <Dialog open={isInventoryDialogOpen} onOpenChange={setIsInventoryDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>{inventoryType === 'global' ? 'Global Inventory' : 'Store Inventory'}</DialogTitle>
            <DialogDescription>Add stock to <span className="font-mono text-primary">{currentVariant?.sku}</span></DialogDescription>
          </DialogHeader>
          <form onSubmit={handleInventorySubmit}>
            <div className="grid gap-4 py-4">
              {inventoryType === 'store' && (
                <div className="grid gap-2">
                  <Label>Select Store *</Label>
                  <Select value={inventoryForm.store_id} onValueChange={v => setInventoryForm(prev => ({ ...prev, store_id: v }))} required>
                    <SelectTrigger><SelectValue placeholder="Choose store" /></SelectTrigger>
                    <SelectContent>{stores.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              )}
              <div className="grid gap-2">
                <Label>Quantity to Add/Set *</Label>
                <Input type="number" min="0" value={inventoryForm.quantity} onChange={e => setInventoryForm(prev => ({ ...prev, quantity: e.target.value }))} required />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsInventoryDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Saving...' : 'Save'}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Other Dialogs (Product, Variant, Image, Delete) */}
      <Dialog open={isProductDialogOpen} onOpenChange={o => { if (!o) resetProductForm(); setIsProductDialogOpen(o); }}>
        <DialogContent className="sm:max-w-[600px]"><DialogHeader><DialogTitle>{editingProduct ? 'Edit' : 'Create'} Product</DialogTitle></DialogHeader>
          <form onSubmit={editingProduct ? handleUpdateProduct : handleCreateProduct}>
            <div className="grid gap-4 py-4">

              <div className="grid grid-cols-2 gap-4"><div className="grid gap-2">
                <Label htmlFor="name">Product Name *</Label>
                <Input
                  id="name"
                  value={productForm.name}
                  onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                  required
                  placeholder="e.g. Air Max 90"
                />
              </div><div className="grid gap-2"><Label>Brand</Label><Input value={productForm.brand} onChange={e => setProductForm({ ...productForm, brand: e.target.value })} required /></div><div className="grid gap-2"><Label>Category</Label><Select value={productForm.category} onValueChange={v => setProductForm({ ...productForm, category: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent></Select></div></div>
              <div className="grid grid-cols-2 gap-4"><div className="grid gap-2"><Label>Gender</Label><Select value={productForm.gender} onValueChange={v => setProductForm({ ...productForm, gender: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{GENDER_OPTIONS.map(g => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}</SelectContent></Select></div><div className="grid gap-2"><Label>Fabric</Label><Input value={productForm.fabric_type} onChange={e => setProductForm({ ...productForm, fabric_type: e.target.value })} /></div></div>
              <div className="grid gap-2"><Label>Description</Label><Textarea value={productForm.description} onChange={e => setProductForm({ ...productForm, description: e.target.value })} required /></div>
            </div>
            <DialogFooter><Button type="submit" disabled={isSubmitting}>Save</Button></DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={isVariantDialogOpen} onOpenChange={o => { if (!o) resetVariantForm(); setIsVariantDialogOpen(o); }}>
        <DialogContent><DialogHeader><DialogTitle>{editingVariant ? 'Edit' : 'Create'} Variant</DialogTitle></DialogHeader>
          <form onSubmit={editingVariant ? handleUpdateVariant : handleCreateVariant}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2"><Label>Product</Label><Select value={variantForm.product_id} onValueChange={v => setVariantForm({ ...variantForm, product_id: v })} disabled={!!editingVariant}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{products.map(p => <SelectItem key={p.id} value={p.id}>{p.brand}</SelectItem>)}</SelectContent></Select></div>
              <div className="grid grid-cols-2 gap-4"><div className="grid gap-2"><Label>SKU</Label><Input value={variantForm.sku} onChange={e => setVariantForm({ ...variantForm, sku: e.target.value })} /></div><div className="grid gap-2"><Label>Price</Label><Input type="number" value={variantForm.base_price} onChange={e => setVariantForm({ ...variantForm, base_price: e.target.value })} /></div></div>
              <div className="grid grid-cols-2 gap-4"><div className="grid gap-2"><Label>Color</Label><Select value={variantForm.color} onValueChange={v => setVariantForm({ ...variantForm, color: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{COLORS.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent></Select></div><div className="grid gap-2"><Label>Size</Label><Select value={variantForm.size} onValueChange={v => setVariantForm({ ...variantForm, size: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{SIZES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent></Select></div></div>
            </div>
            <DialogFooter><Button type="submit" disabled={isSubmitting}>Save</Button></DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={isImageDialogOpen} onOpenChange={setIsImageDialogOpen}>
        <DialogContent><DialogHeader><DialogTitle>Add Image</DialogTitle></DialogHeader>
          <form onSubmit={handleImageUpload}>
            <div className="grid gap-4 py-4"><Input type="file" onChange={handleFileChange} accept="image/*" /><Input type="number" placeholder="Position" value={imageForm.position} onChange={e => setImageForm({ position: e.target.value })} /></div>
            <DialogFooter><Button type="submit" disabled={uploadingImage}>Upload</Button></DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent><DialogHeader><DialogTitle>Confirm Delete</DialogTitle><DialogDescription>Delete {deletingItem.name}?</DialogDescription></DialogHeader>
          <DialogFooter><Button variant="destructive" onClick={deletingItem.type === 'product' ? handleDeleteProduct : handleDeleteVariant} disabled={isSubmitting}>Delete</Button></DialogFooter></DialogContent>
      </Dialog>
    </div>
  );
}