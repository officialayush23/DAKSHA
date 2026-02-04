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
  X
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
  const [variants, setVariants] = useState({});
  const [loading, setLoading] = useState(true);
  const [variantsLoading, setVariantsLoading] = useState({});
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [viewMode, setViewMode] = useState("list");
  
  // Dialog States
  const [isProductDialogOpen, setIsProductDialogOpen] = useState(false);
  const [isVariantDialogOpen, setIsVariantDialogOpen] = useState(false);
  const [isImageDialogOpen, setIsImageDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Expanded products for tree view
  const [expandedProducts, setExpandedProducts] = useState({});
  
  // Current item being edited/deleted
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingVariant, setEditingVariant] = useState(null);
  const [deletingItem, setDeletingItem] = useState({ type: '', id: '', name: '' });
  const [currentVariant, setCurrentVariant] = useState(null);
  
  // Image upload state
  const [uploadingImage, setUploadingImage] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  // Simplified options
  const GENDER_OPTIONS = [
    { value: "male", label: "Male" },
    { value: "female", label: "Female" },
    { value: "unisex", label: "Unisex" },
    { value: "kids", label: "Kids" }
  ];

  const CATEGORIES = [
    "Shoes", "Clothing", "Accessories", "Bags", "Jewelry",
    "Watches", "Eyewear", "Fragrances", "Skincare", "Home"
  ];

  const SIZES = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"];
  const COLORS = [
    "Black", "White", "Red", "Blue", "Green", 
    "Yellow", "Purple", "Pink", "Orange", "Brown"
  ];

  // Form States
  const [productForm, setProductForm] = useState({
    brand: "",
    category: "",
    gender: "",
    fabric_type: "",
    description: "",
    occasion: "",
    active: true
  });

  const [variantForm, setVariantForm] = useState({
    product_id: "",
    sku: "",
    color: "",
    size: "",
    base_price: "",
    active: true
  });

  const [imageForm, setImageForm] = useState({
    position: 0
  });

  // Available categories from products
  const categories = Array.from(new Set(products.map(p => p.category).filter(Boolean)));

  // --- Fetch Functions ---
  const fetchProducts = async () => {
    try {
      setLoading(true);
      const productsList = await AdminService.listProducts();
      setProducts(Array.isArray(productsList) ? productsList : []);
      toast.success("Products loaded successfully");
    } catch (error) {
      console.error("Failed to fetch products:", error);
      toast.error("Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  const fetchVariants = async (productId) => {
    try {
      setVariantsLoading(prev => ({ ...prev, [productId]: true }));
      const variantsList = await AdminService.listVariants(productId);
      setVariants(prev => ({ 
        ...prev, 
        [productId]: Array.isArray(variantsList) ? variantsList : [] 
      }));
    } catch (error) {
      console.error(`Failed to fetch variants for product ${productId}:`, error);
      setVariants(prev => ({ ...prev, [productId]: [] }));
      toast.error(`Failed to load variants for product`);
    } finally {
      setVariantsLoading(prev => ({ ...prev, [productId]: false }));
    }
  };

  // --- Product CRUD ---
  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const cleanFormData = {
        brand: productForm.brand.trim(),
        category: productForm.category.trim(),
        gender: productForm.gender.trim(),
        fabric_type: productForm.fabric_type.trim(),
        description: productForm.description.trim(),
        occasion: productForm.occasion.trim()
      };

      await AdminService.createProduct(cleanFormData);
      toast.success("Product created successfully");
      resetProductForm();
      setIsProductDialogOpen(false);
      fetchProducts();
    } catch (error) {
      console.error("Failed to create product:", error);
      toast.error(`Failed to create product: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateProduct = async (e) => {
    e.preventDefault();
    if (!editingProduct) return;
    
    setIsSubmitting(true);
    try {
      const cleanFormData = {
        brand: productForm.brand.trim(),
        category: productForm.category.trim(),
        gender: productForm.gender.trim(),
        fabric_type: productForm.fabric_type.trim(),
        description: productForm.description.trim(),
        occasion: productForm.occasion.trim(),
        active: productForm.active
      };

      await AdminService.updateProduct(editingProduct.id, cleanFormData);
      toast.success("Product updated successfully");
      resetProductForm();
      setEditingProduct(null);
      setIsProductDialogOpen(false);
      fetchProducts();
    } catch (error) {
      console.error("Failed to update product:", error);
      toast.error(`Failed to update product: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteProduct = async () => {
    if (!deletingItem.id) return;
    
    setIsSubmitting(true);
    try {
      await AdminService.deleteProduct(deletingItem.id);
      toast.success("Product deleted successfully");
      setIsDeleteDialogOpen(false);
      setDeletingItem({ type: '', id: '', name: '' });
      fetchProducts();
    } catch (error) {
      console.error("Failed to delete product:", error);
      toast.error("Failed to delete product");
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- Variant CRUD ---
  const handleCreateVariant = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const variantData = {
        product_id: variantForm.product_id,
        sku: variantForm.sku.trim(),
        color: variantForm.color.trim(),
        size: variantForm.size.trim(),
        base_price: parseFloat(variantForm.base_price) || 0
      };

      await AdminService.createVariant(variantData);
      toast.success("Variant created successfully");
      resetVariantForm();
      setIsVariantDialogOpen(false);
      
      if (variantForm.product_id) {
        fetchVariants(variantForm.product_id);
      }
    } catch (error) {
      console.error("Failed to create variant:", error);
      toast.error("Failed to create variant");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateVariant = async (e) => {
    e.preventDefault();
    if (!editingVariant) return;
    
    setIsSubmitting(true);
    try {
      const variantData = {
        color: variantForm.color.trim(),
        size: variantForm.size.trim(),
        base_price: parseFloat(variantForm.base_price) || 0,
        active: variantForm.active
      };

      await AdminService.updateVariant(editingVariant.id, variantData);
      toast.success("Variant updated successfully");
      resetVariantForm();
      setEditingVariant(null);
      setIsVariantDialogOpen(false);
      
      if (variantForm.product_id) {
        fetchVariants(variantForm.product_id);
      }
    } catch (error) {
      console.error("Failed to update variant:", error);
      toast.error("Failed to update variant");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteVariant = async () => {
    if (!deletingItem.id) return;
    
    setIsSubmitting(true);
    try {
      await AdminService.deleteVariant(deletingItem.id);
      toast.success("Variant deleted successfully");
      setIsDeleteDialogOpen(false);
      setDeletingItem({ type: '', id: '', name: '' });
      
      const variant = variants[deletingItem.productId]?.find(v => v.id === deletingItem.id);
      if (variant) {
        fetchVariants(variant.product_id);
      }
    } catch (error) {
      console.error("Failed to delete variant:", error);
      toast.error("Failed to delete variant");
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- Image Upload ---
  const handleImageUpload = async (e) => {
    e.preventDefault();
    if (!currentVariant || !imageFile) return;
    
    setUploadingImage(true);
    try {
      // First, upload the image file to your server
      const formData = new FormData();
      formData.append('file', imageFile);
      
      // Assuming you have an endpoint for file uploads
      // Replace with your actual upload endpoint
      const uploadResponse = await fetch('http://localhost:8000/admin/upload', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`
        }
      });
      
      if (!uploadResponse.ok) {
        throw new Error('Failed to upload image');
      }
      
      const { image_url } = await uploadResponse.json();
      
      // Then add the image to variant
      const imageData = {
        image_url: image_url,
        position: parseInt(imageForm.position) || 0
      };

      await AdminService.addImage(currentVariant.id, imageData);
      toast.success("Image added successfully");
      resetImageForm();
      setIsImageDialogOpen(false);
      
      // Refresh variants for the product
      if (currentVariant.product_id) {
        fetchVariants(currentVariant.product_id);
      }
    } catch (error) {
      console.error("Failed to add image:", error);
      toast.error("Failed to add image");
    } finally {
      setUploadingImage(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image size should be less than 5MB');
      return;
    }

    setImageFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  // --- Helper Functions ---
  const toggleProductExpansion = async (productId) => {
    const isExpanded = expandedProducts[productId];
    setExpandedProducts(prev => ({ ...prev, [productId]: !isExpanded }));
    
    if (!isExpanded && !variants[productId]) {
      await fetchVariants(productId);
    }
  };

  const resetProductForm = () => {
    setProductForm({
      brand: "",
      category: "",
      gender: "",
      fabric_type: "",
      description: "",
      occasion: "",
      active: true
    });
  };

  const resetVariantForm = () => {
    setVariantForm({
      product_id: "",
      sku: "",
      color: "",
      size: "",
      base_price: "",
      active: true
    });
  };

  const resetImageForm = () => {
    setImageForm({ position: 0 });
    setImageFile(null);
    setImagePreview(null);
    setCurrentVariant(null);
  };

  const openEditProductDialog = (product) => {
    setEditingProduct(product);
    setProductForm({
      brand: product.brand || "",
      category: product.category || "",
      gender: product.gender || "",
      fabric_type: product.fabric_type || "",
      description: product.description || "",
      occasion: product.occasion || "",
      active: product.active !== false
    });
    setIsProductDialogOpen(true);
  };

  const openEditVariantDialog = (variant, productId) => {
    setEditingVariant(variant);
    setVariantForm({
      product_id: productId,
      sku: variant.sku || "",
      color: variant.color || "",
      size: variant.size || "",
      base_price: variant.base_price?.toString() || "",
      active: variant.active !== false
    });
    setIsVariantDialogOpen(true);
  };

  const openAddImageDialog = (variant) => {
    setCurrentVariant(variant);
    setIsImageDialogOpen(true);
  };

  const openDeleteDialog = (type, id, name, productId = null) => {
    setDeletingItem({ type, id, name, productId });
    setIsDeleteDialogOpen(true);
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const filteredProducts = products.filter(product => {
    const matchesSearch = 
      product.brand?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.description?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = filterCategory === "all" || product.category === filterCategory;
    const matchesStatus = filterStatus === "all" || 
      (filterStatus === "active" && product.active !== false) ||
      (filterStatus === "inactive" && product.active === false);
    
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const calculateStats = () => {
    const totalVariants = Object.values(variants).flat().length;
    const activeProducts = products.filter(p => p.active !== false).length;
    const productsWithVariants = Object.keys(variants).filter(productId => variants[productId]?.length > 0).length;
    const totalCategories = categories.length;
    
    return {
      totalProducts: products.length,
      totalVariants,
      activeProducts,
      productsWithVariants,
      totalCategories,
      averageVariantsPerProduct: products.length > 0 ? (totalVariants / products.length).toFixed(1) : 0
    };
  };

  const stats = calculateStats();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Products Management</h1>
          <p className="text-muted-foreground">Manage products and variants</p>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Button
              variant={viewMode === "list" ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode("list")}
              className="h-8 w-8 p-0"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              size="sm"
              onClick={() => setViewMode("grid")}
              className="h-8 w-8 p-0"
            >
              <Grid3x3 className="h-4 w-4" />
            </Button>
          </div>
          
          <Button variant="outline" size="sm" onClick={fetchProducts} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button onClick={() => setIsProductDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> Add Product
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Products</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalProducts}</div>
            <div className="text-xs text-muted-foreground">
              {stats.activeProducts} active
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Variants</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalVariants}</div>
            <div className="text-xs text-muted-foreground">
              Avg. {stats.averageVariantsPerProduct} per product
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">With Variants</CardTitle>
            <Grid3x3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.productsWithVariants}</div>
            <Progress value={(stats.productsWithVariants / stats.totalProducts) * 100} className="mt-2" />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalCategories}</div>
            <div className="text-xs text-muted-foreground">
              Unique categories
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search products..."
              className="pl-9"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        <div className="flex gap-2">
          <Select value={filterCategory} onValueChange={setFilterCategory}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories.map(category => (
                <SelectItem key={category} value={category}>{category}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Products Tree View */}
      {viewMode === "list" ? (
        <div className="rounded-md border bg-card">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="text-center">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">Loading products...</p>
              </div>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-12">
              <Package className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <h3 className="text-lg font-medium mb-2">No products found</h3>
              <p className="text-muted-foreground mb-4">Try adjusting your search or create a new product</p>
              <Button onClick={() => setIsProductDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" /> Create Product
              </Button>
            </div>
          ) : (
            <div className="divide-y">
              {filteredProducts.map((product) => {
                const isExpanded = expandedProducts[product.id];
                const productVariants = variants[product.id] || [];
                const isLoading = variantsLoading[product.id];
                
                return (
                  <Collapsible 
                    key={product.id} 
                    open={isExpanded}
                    onOpenChange={() => toggleProductExpansion(product.id)}
                  >
                    {/* Product Row */}
                    <div className="p-4 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <CollapsibleTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          </CollapsibleTrigger>
                          
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-full bg-blue-100 dark:bg-blue-900/30">
                              <Package className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            </div>
                            
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium">{product.brand}</h3>
                                <span className="text-muted-foreground">•</span>
                                <span className="font-medium text-primary">{product.category}</span>
                                {product.gender && (
                                  <Badge variant="outline">{product.gender}</Badge>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground line-clamp-1">
                                {product.description || "No description"}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                          <div className="hidden md:flex items-center gap-4">
                            <div className="text-right">
                              <div className="text-sm font-medium">
                                {productVariants.length} variants
                              </div>
                              <div className="text-xs text-muted-foreground">
                                ID: {product.id?.slice(0, 8)}...
                              </div>
                            </div>
                            
                            <Badge variant={product.active !== false ? "default" : "secondary"}>
                              {product.active !== false ? "Active" : "Inactive"}
                            </Badge>
                          </div>
                          
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuItem onClick={() => openEditProductDialog(product)}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit Product
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => {
                                setVariantForm(prev => ({ ...prev, product_id: product.id }));
                                setIsVariantDialogOpen(true);
                              }}>
                                <Plus className="mr-2 h-4 w-4" />
                                Add Variant
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => navigator.clipboard.writeText(product.id)}>
                                <Copy className="mr-2 h-4 w-4" />
                                Copy ID
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-destructive"
                                onClick={() => openDeleteDialog('product', product.id, `${product.brand} - ${product.category}`)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete Product
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    </div>
                    
                    {/* Variants Content */}
                    <CollapsibleContent>
                      <div className="px-4 pb-4">
                        <div className="border rounded-lg bg-muted/30">
                          {isLoading ? (
                            <div className="flex justify-center items-center h-32">
                              <Loader2 className="h-6 w-6 animate-spin" />
                            </div>
                          ) : productVariants.length === 0 ? (
                            <div className="text-center py-8">
                              <Palette className="h-8 w-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                              <p className="text-muted-foreground mb-4">No variants created yet</p>
                              <Button 
                                size="sm"
                                onClick={() => {
                                  setVariantForm(prev => ({ ...prev, product_id: product.id }));
                                  setIsVariantDialogOpen(true);
                                }}
                              >
                                <Plus className="mr-2 h-3 w-3" />
                                Create First Variant
                              </Button>
                            </div>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow className="bg-muted/50">
                                  <TableHead>SKU</TableHead>
                                  <TableHead>Color</TableHead>
                                  <TableHead>Size</TableHead>
                                  <TableHead>Price</TableHead>
                                  <TableHead>Status</TableHead>
                                  <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {productVariants.map((variant) => (
                                  <TableRow key={variant.id}>
                                    <TableCell className="font-mono text-xs">
                                      {variant.sku}
                                    </TableCell>
                                    <TableCell>
                                      <div className="flex items-center gap-2">
                                        {variant.color && (
                                          <>
                                            <div 
                                              className="h-3 w-3 rounded-full border"
                                              style={{ backgroundColor: variant.color.toLowerCase() }}
                                            />
                                            <span>{variant.color}</span>
                                          </>
                                        )}
                                      </div>
                                    </TableCell>
                                    <TableCell>
                                      {variant.size ? (
                                        <Badge variant="outline">{variant.size}</Badge>
                                      ) : (
                                        <span className="text-muted-foreground">-</span>
                                      )}
                                    </TableCell>
                                    <TableCell className="font-medium">
                                      ₹{variant.base_price?.toFixed(2) || "0.00"}
                                    </TableCell>
                                    <TableCell>
                                      <Badge variant={variant.active !== false ? "default" : "secondary"}>
                                        {variant.active !== false ? "Active" : "Inactive"}
                                      </Badge>
                                    </TableCell>
                                    <TableCell className="text-right">
                                      <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                            <MoreHorizontal className="h-4 w-4" />
                                          </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                          <DropdownMenuItem onClick={() => openEditVariantDialog(variant, product.id)}>
                                            <Edit className="mr-2 h-4 w-4" />
                                            Edit Variant
                                          </DropdownMenuItem>
                                          <DropdownMenuItem onClick={() => openAddImageDialog(variant)}>
                                            <ImageIcon className="mr-2 h-4 w-4" />
                                            Add Images
                                          </DropdownMenuItem>
                                          <DropdownMenuItem 
                                            onClick={() => navigator.clipboard.writeText(variant.id)}
                                          >
                                            <Copy className="mr-2 h-4 w-4" />
                                            Copy ID
                                          </DropdownMenuItem>
                                          <DropdownMenuSeparator />
                                          <DropdownMenuItem 
                                            className="text-destructive"
                                            onClick={() => openDeleteDialog('variant', variant.id, variant.sku, product.id)}
                                          >
                                            <Trash2 className="mr-2 h-4 w-4" />
                                            Delete Variant
                                          </DropdownMenuItem>
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
      ) : (
        /* Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProducts.map((product) => (
            <Card key={product.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{product.brand}</CardTitle>
                    <CardDescription>{product.category}</CardDescription>
                  </div>
                  <Badge variant={product.active !== false ? "default" : "secondary"}>
                    {product.active !== false ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{product.gender || 'Unisex'}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {product.description || 'No description'}
                  </p>
                  <div className="flex items-center justify-between pt-2">
                    <div>
                      <div className="text-xs text-muted-foreground">Variants</div>
                      <div className="text-sm font-medium">
                        {(variants[product.id] || []).length}
                      </div>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => toggleProductExpansion(product.id)}
                    >
                      {expandedProducts[product.id] ? 'Hide' : 'View'} Details
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Product Dialog */}
      <Dialog open={isProductDialogOpen} onOpenChange={(open) => {
        if (!open) {
          resetProductForm();
          setEditingProduct(null);
        }
        setIsProductDialogOpen(open);
      }}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>{editingProduct ? 'Edit Product' : 'Create Product'}</DialogTitle>
            <DialogDescription>
              {editingProduct ? 'Update product details' : 'Add a new product'}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={editingProduct ? handleUpdateProduct : handleCreateProduct}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="brand">Brand *</Label>
                  <Input 
                    id="brand" 
                    placeholder="e.g. Nike, Adidas" 
                    value={productForm.brand} 
                    onChange={(e) => setProductForm(prev => ({ ...prev, brand: e.target.value }))}
                    required 
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="category">Category *</Label>
                  <Select 
                    value={productForm.category} 
                    onValueChange={(value) => setProductForm(prev => ({ ...prev, category: value }))}
                    required
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map(category => (
                        <SelectItem key={category} value={category}>{category}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="gender">Gender</Label>
                  <Select 
                    value={productForm.gender} 
                    onValueChange={(value) => setProductForm(prev => ({ ...prev, gender: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      {GENDER_OPTIONS.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="fabric_type">Fabric Type</Label>
                  <Input 
                    id="fabric_type" 
                    placeholder="e.g. Cotton, Polyester" 
                    value={productForm.fabric_type} 
                    onChange={(e) => setProductForm(prev => ({ ...prev, fabric_type: e.target.value }))}
                  />
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="occasion">Occasion</Label>
                <Input 
                  id="occasion" 
                  placeholder="e.g. Casual, Formal" 
                  value={productForm.occasion} 
                  onChange={(e) => setProductForm(prev => ({ ...prev, occasion: e.target.value }))}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="description">Description *</Label>
                <Textarea 
                  id="description" 
                  placeholder="Product description..." 
                  value={productForm.description} 
                  onChange={(e) => setProductForm(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  required
                />
              </div>

              {editingProduct && (
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Active Status</Label>
                    <p className="text-sm text-muted-foreground">Make this product available</p>
                  </div>
                  <Switch 
                    checked={productForm.active}
                    onCheckedChange={(checked) => setProductForm(prev => ({ ...prev, active: checked }))}
                  />
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setIsProductDialogOpen(false);
                  resetProductForm();
                  setEditingProduct(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingProduct ? 'Update Product' : 'Create Product'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Variant Dialog */}
      <Dialog open={isVariantDialogOpen} onOpenChange={(open) => {
        if (!open) {
          resetVariantForm();
          setEditingVariant(null);
        }
        setIsVariantDialogOpen(open);
      }}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>{editingVariant ? 'Edit Variant' : 'Create Variant'}</DialogTitle>
            <DialogDescription>
              {editingVariant ? 'Update variant details' : 'Add a new variant to product.'}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={editingVariant ? handleUpdateVariant : handleCreateVariant}>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="product_id">Select Product *</Label>
                <Select 
                  value={variantForm.product_id} 
                  onValueChange={(value) => setVariantForm(prev => ({ ...prev, product_id: value }))}
                  required
                  disabled={!!editingVariant}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map(product => (
                      <SelectItem key={product.id} value={product.id}>
                        <div className="flex items-center gap-2">
                          <Package className="h-3 w-3" />
                          <span>{product.brand} - {product.category}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="sku">SKU *</Label>
                  <Input 
                    id="sku" 
                    placeholder="e.g. NIKE-M-BLK-10" 
                    value={variantForm.sku}
                    onChange={(e) => setVariantForm(prev => ({ ...prev, sku: e.target.value }))}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="base_price">Base Price (₹) *</Label>
                  <Input 
                    id="base_price" 
                    type="number" 
                    placeholder="0.00" 
                    value={variantForm.base_price}
                    onChange={(e) => setVariantForm(prev => ({ ...prev, base_price: e.target.value }))}
                    min="0"
                    step="0.01"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="color">Color</Label>
                  <Select 
                    value={variantForm.color} 
                    onValueChange={(value) => setVariantForm(prev => ({ ...prev, color: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select color" />
                    </SelectTrigger>
                    <SelectContent>
                      {COLORS.map(color => (
                        <SelectItem key={color} value={color}>
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full border"
                              style={{ 
                                backgroundColor: color.toLowerCase(),
                                border: '1px solid #ccc'
                              }}
                            />
                            {color}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="size">Size</Label>
                  <Select 
                    value={variantForm.size} 
                    onValueChange={(value) => setVariantForm(prev => ({ ...prev, size: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select size" />
                    </SelectTrigger>
                    <SelectContent>
                      {SIZES.map(size => (
                        <SelectItem key={size} value={size}>{size}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {editingVariant && (
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Active Status</Label>
                    <p className="text-sm text-muted-foreground">Make this variant available</p>
                  </div>
                  <Switch 
                    checked={variantForm.active}
                    onCheckedChange={(checked) => setVariantForm(prev => ({ ...prev, active: checked }))}
                  />
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setIsVariantDialogOpen(false);
                  resetVariantForm();
                  setEditingVariant(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingVariant ? 'Update Variant' : 'Create Variant'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Image Upload Dialog */}
      <Dialog open={isImageDialogOpen} onOpenChange={setIsImageDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add Image to Variant</DialogTitle>
            <DialogDescription>
              Upload image for variant: <span className="font-mono text-xs">{currentVariant?.sku}</span>
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleImageUpload}>
            <div className="grid gap-4 py-4">
              {/* File Upload */}
              <div className="grid gap-2">
                <Label htmlFor="image">Image File *</Label>
                <div className="border-2 border-dashed rounded-lg p-6 text-center">
                  {imagePreview ? (
                    <div className="space-y-4">
                      <div className="relative mx-auto w-48 h-48">
                        <img 
                          src={imagePreview} 
                          alt="Preview" 
                          className="w-full h-full object-contain rounded-md"
                        />
                        <Button
                          type="button"
                          variant="destructive"
                          size="sm"
                          className="absolute -top-2 -right-2 h-6 w-6 p-0 rounded-full"
                          onClick={() => {
                            setImageFile(null);
                            setImagePreview(null);
                          }}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {imageFile?.name}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">Click to upload or drag and drop</p>
                        <p className="text-xs text-muted-foreground">
                          PNG, JPG, GIF up to 5MB
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="mt-2"
                        onClick={() => document.getElementById('file-upload').click()}
                      >
                        Select Image
                      </Button>
                      <input
                        id="file-upload"
                        type="file"
                        className="hidden"
                        accept="image/*"
                        onChange={handleFileChange}
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="position">Display Position</Label>
                <Input 
                  id="position" 
                  type="number" 
                  min="0"
                  value={imageForm.position}
                  onChange={(e) => setImageForm(prev => ({ ...prev, position: parseInt(e.target.value) || 0 }))}
                />
                <p className="text-xs text-muted-foreground">
                  Lower numbers appear first (0 = primary image)
                </p>
              </div>
            </div>
            
            <DialogFooter>
              <Button 
                type="button" 
                variant="outline" 
                onClick={resetImageForm}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={!imageFile || uploadingImage}>
                {uploadingImage && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Upload Image
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Confirm Deletion</DialogTitle>
            <DialogDescription>
              This action cannot be undone. This will permanently delete the {deletingItem.type}.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div>
                <p className="font-medium">Are you sure you want to delete?</p>
                <p className="text-sm text-muted-foreground">{deletingItem.name}</p>
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => {
                setIsDeleteDialogOpen(false);
                setDeletingItem({ type: '', id: '', name: '' });
              }}
            >
              Cancel
            </Button>
            <Button 
              type="button" 
              variant="destructive"
              onClick={deletingItem.type === 'product' ? handleDeleteProduct : handleDeleteVariant}
              disabled={isSubmitting}
            >
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete {deletingItem.type}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}