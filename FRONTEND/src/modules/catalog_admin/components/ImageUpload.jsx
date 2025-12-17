// ImageUpload.jsx

import React, { useState } from "react";
import { UploadCloud, X, Loader2, Image as ImageIcon } from "lucide-react";
import { catalogService } from "@/services/catalogService";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

export default function ImageUpload({ onUploadComplete, currentImage }) {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(currentImage || null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 1. Client-side validation
    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      toast.error("File size too large. Max 5MB.");
      return;
    }

    // 2. Show local preview immediately
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    setUploading(true);

    try {
      // 3. Upload to Server/Supabase
      const publicUrl = await catalogService.uploadImage(file);
      
      // 4. Pass URL back to parent form
      onUploadComplete(publicUrl);
      toast.success("Image uploaded successfully");
    } catch (error) {
      console.error("Upload failed", error);
      toast.error("Failed to upload image.");
      setPreview(null); // Revert on failure
    } finally {
      setUploading(false);
    }
  };

  const handleRemove = () => {
    setPreview(null);
    onUploadComplete(""); // Clear in parent
  };

  return (
    <div className="w-full space-y-4">
      {preview ? (
        <div className="relative group w-full h-64 border rounded-lg overflow-hidden bg-slate-100 dark:bg-slate-900 flex items-center justify-center">
          <img 
            src={preview} 
            alt="Product Preview" 
            className="h-full w-full object-contain"
          />
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button 
              variant="destructive" 
              size="icon" 
              onClick={handleRemove}
              type="button"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          {uploading && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-white" />
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center w-full">
          <label 
            htmlFor="dropzone-file" 
            className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 dark:bg-gray-900 dark:border-gray-800 dark:hover:border-gray-700 dark:hover:bg-gray-800 transition-all"
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6 text-muted-foreground">
              <UploadCloud className="w-10 h-10 mb-3" />
              <p className="text-sm font-semibold">Click to upload product image</p>
              <p className="text-xs">SVG, PNG, JPG or WEBP (MAX. 5MB)</p>
            </div>
            <input 
              id="dropzone-file" 
              type="file" 
              className="hidden" 
              accept="image/*"
              onChange={handleFileChange}
              disabled={uploading}
            />
          </label>
        </div>
      )}
    </div>
  );
}